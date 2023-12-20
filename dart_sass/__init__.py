from .compiler import Compiler, Syntax, OutputStyle
from .importer import Importer

def compile_string(
        source,
        url="",
        syntax=Syntax.SCSS,
        style=OutputStyle.COMPRESSED,
        source_map=False,
        source_map_include_sources=False,
        charset=False,
        importers=None):
    compiler = Compiler()
    
    if importers is None:
        importers = []

    for importer in importers:
        compiler.add_importer(importer)
    
    return compiler.compile_string(
        source=source,
        url=url,
        syntax=syntax,
        style=style,
        source_map=source_map,
        source_map_include_sources=source_map_include_sources,
        charset=charset,
    )
    
    