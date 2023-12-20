from .proto.embedded_sass_pb2 import InboundMessage, OutboundMessage, Syntax, OutputStyle
import subprocess
from google.protobuf.internal import encoder, decoder
from . import _varint
from .importer import Importer

class CompilationError(Exception):
    pass

class Compiler:
    def __init__(self):
        self.importers = []
        self.sass_process = subprocess.Popen(
            ["sass", "--embedded"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        self.compilation_id = 1
        
    def add_importer(self, importer):
        self.importers.append(importer)
        
    def _write_message(self, compilation_id, message):
        length = message.ByteSize()
        
        self.sass_process.stdin.write(
            encoder._VarintBytes(length + 1) 
            + bytes([compilation_id]) + message.SerializeToString())
        self.sass_process.stdin.flush()
        
    def _read_message(self):
        readable = self.sass_process.stdout
        length = _varint.read(readable)
        compilation_id = ord(readable.read(1))
        output = readable.read(length - 1)
        outbound_message = OutboundMessage()
        outbound_message.ParseFromString(output)
        return (compilation_id, outbound_message)

    def compile_string(
        self,
        source,
        url="",
        syntax=Syntax.SCSS,
        style=OutputStyle.COMPRESSED,
        source_map=False,
        source_map_include_sources=False,
        charset=False,
    ):
        importers = [
            InboundMessage.CompileRequest.Importer(
                importer_id=ix
            ) for ix, importer in enumerate(self.importers)
        ]
        
        compilation_id = ++self.compilation_id
        compile_request = InboundMessage.CompileRequest(
            string={
                "source": source,
                "url": url,
                "syntax": syntax,
            },
            path=None,
            style=style,
            source_map=source_map,
            importers=importers,
            global_functions=[],
            alert_color=False,
            alert_ascii=False,
            verbose=False,
            quiet_deps=False,
            source_map_include_sources=source_map_include_sources,
            charset=charset,
        )

        message = InboundMessage(
            compile_request=compile_request,
        )
        
        self._write_message(
            compilation_id=compilation_id, message=message
        )
        
        while True:
            # communication loop to read messages and respond accordingly
            response = self._read_message()[1]
            response_type = response.WhichOneof('message')
            
            if response_type == 'compile_response':
                return self._handle_compile_response(
                    response.compile_response)
            elif response_type == 'canonicalize_request':
                next_message = self._handle_canonicalize_request(
                    response.canonicalize_request)
            elif response_type == 'import_request':
                next_message = self._handle_import_request(
                    response.import_request
                )
                    
            self._write_message(
                compilation_id=compilation_id, message=next_message
            )
            
    def _handle_compile_response(self, response):
        result = response.WhichOneof('result')
        if result == 'success':
            success = response.success
            css = success.css
            source_map = success.source_map
            return {'css': css, 'source_map': source_map}
        elif result == 'failure':
            failure = response.failure
            raise CompilationError(failure.formatted)
        
    def _handle_canonicalize_request(self, request):
        url = self.importers[
            request.importer_id].canonicalize(
                url=request.url,
                from_import=request.from_import,
                containing_url=request.containing_url
            )
        response = InboundMessage.CanonicalizeResponse(
            id=request.id,
            url=url
        )
        
        return InboundMessage(canonicalize_response=response)
    
    def _handle_import_request(self, request):
        load_res = self.importers[
            request.importer_id].load(
                url=request.url,
            )
        contents, syntax, source_map_url = (list(load_res) + ['']*3)[:3]
        response = InboundMessage.ImportResponse(
            id=request.id,
            success=InboundMessage.ImportResponse.ImportSuccess(
                contents=contents,
                syntax=syntax,
                source_map_url=source_map_url
            )
        )
        return InboundMessage(import_response=response)

