from typing import Optional, Dict, Any
from app.core.logging import logger

_js_parser = None
_java_parser = None

def get_js_parser():
    global _js_parser
    if _js_parser is None:
        try:
            import tree_sitter
            import tree_sitter_javascript as tsjs
            lang = tree_sitter.Language(tsjs.language())
            _js_parser = tree_sitter.Parser(lang)
        except Exception as e:
            logger.error(f"Failed to initialize Tree-sitter JavaScript parser: {e}")
            return None
    return _js_parser

def get_java_parser():
    global _java_parser
    if _java_parser is None:
        try:
            import tree_sitter
            import tree_sitter_java as tsjava
            lang = tree_sitter.Language(tsjava.language())
            _java_parser = tree_sitter.Parser(lang)
        except Exception as e:
            logger.error(f"Failed to initialize Tree-sitter Java parser: {e}")
            return None
    return _java_parser

def parse_code_tree(parser, code_str: str):
    if not parser or not code_str:
        return None
    try:
        code_bytes = code_str.encode("utf-8")
        tree = parser.parse(code_bytes)
        return tree.root_node
    except Exception as e:
        logger.warning(f"Tree-sitter parse error: {e}")
        return None

def get_node_text(node, code_str: str) -> str:
    if not node or not code_str:
        return ""
    try:
        start = node.start_byte
        end = node.end_byte
        return code_str.encode("utf-8")[start:end].decode("utf-8", errors="ignore").strip()
    except Exception:
        return ""
