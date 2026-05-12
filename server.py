#!/usr/bin/env python3
"""
MiniLang Compiler — Web Visualizer Server
============================================
HTTP server that powers the interactive compiler visualizer.
Serves the static frontend and provides API endpoints for compilation.
"""

import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.compiler import Compiler
from src.lexer import Lexer
from src.parser import Parser
from src.semantic import SemanticAnalyzer
from src.vm import VM
from src.errors import CompilerError


class VisualizerHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for the compiler visualizer."""

    def __init__(self, *args, **kwargs):
        # Serve files from the visualizer directory
        super().__init__(*args, directory=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'visualizer'
        ), **kwargs)

    def do_POST(self):
        """Handle POST requests for compilation."""
        if self.path == '/api/compile':
            self._handle_compile()
        elif self.path == '/api/run':
            self._handle_run()
        else:
            self.send_error(404, "Not Found")

    def _handle_compile(self):
        """Compile source code and return all stage results."""
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode('utf-8')

        try:
            data = json.loads(body)
            source = data.get('source', '')

            compiler = Compiler()
            stages = compiler.compile_step_by_step(source)

            result = compiler.stages_to_json(stages)
            result['success'] = True

            self._send_json(result)

        except CompilerError as e:
            partial = self._build_partial_result(source)
            partial.update({
                'success': False,
                'partial': True,
                'error': str(e),
                'error_type': type(e).__name__,
            })
            self._send_json(partial)
        except Exception as e:
            self._send_json({
                'success': False,
                'error': str(e),
                'error_type': 'InternalError',
            })

    def _handle_run(self):
        """Compile and run source code, returning output."""
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode('utf-8')

        try:
            data = json.loads(body)
            source = data.get('source', '')
            inputs = data.get('inputs', [])

            compiler = Compiler()
            stages = compiler.compile_step_by_step(source)

            vm = VM(stages['bytecode'], stages['functions'], trace=True)
            vm.input_callback = lambda: (_ for _ in ()).throw(
                CompilerError("Program requested input(), but no runtime input values were provided.")
            )
            output = vm.run(inputs)

            result = compiler.stages_to_json(stages)
            result['success'] = True
            result['output'] = output
            result['trace'] = vm.trace_log[-100:]
            result['steps'] = vm.step_count
            result['output_note'] = ''

            if len(output) == 0:
                has_print_instruction = any(
                    str(instr).startswith('PRINT')
                    for instr in stages.get('bytecode', [])
                )
                if has_print_instruction:
                    result['output_note'] = (
                        'Program ran successfully, but no PRINT instructions were executed '
                        '(for example, due to control flow).'
                    )
                else:
                    result['output_note'] = (
                        'Program ran successfully. No output was produced because the code '
                        'does not print anything.'
                    )

            self._send_json(result)

        except CompilerError as e:
            partial = self._build_partial_result(source)
            partial.update({
                'success': False,
                'partial': True,
                'error': str(e),
                'error_type': type(e).__name__,
            })
            self._send_json(partial)
        except Exception as e:
            self._send_json({
                'success': False,
                'error': str(e),
                'error_type': 'InternalError',
            })

    def _serialize_tokens(self, tokens):
        """Convert lexer tokens to JSON-safe dictionaries."""
        return [
            {
                'type': t.type.name,
                'value': repr(t.value) if isinstance(t.value, str) else str(t.value),
                'line': t.line,
                'column': t.column,
            }
            for t in tokens
        ]

    def _build_partial_result(self, source: str):
        """Compile incrementally and return whatever stages succeeded."""
        result = {
            'tokens': [],
            'ast': 'Unavailable',
            'symbol_table': 'Unavailable',
            'tac': [],
            'optimized_tac': [],
            'optimization_report': [],
            'bytecode': [],
            'functions': {},
            'output': [],
            'trace': [],
            'steps': 0,
            'failed_stage': 'unknown',
        }

        # Stage 1: lexical analysis
        try:
            tokens = Lexer(source).tokenize()
            result['tokens'] = self._serialize_tokens(tokens)
        except CompilerError:
            result['failed_stage'] = 'lexical'
            return result

        # Stage 2: parsing
        try:
            parser = Parser(tokens)
            ast = parser.parse()
            result['ast'] = ast.pretty_print()
            if hasattr(ast, 'parsing_metadata'):
                result['parsing_metadata'] = ast.parsing_metadata
        except CompilerError:
            result['failed_stage'] = 'syntax'
            return result

        # Stage 3: semantic analysis
        analyzer = SemanticAnalyzer()
        try:
            analyzer.analyze(ast)
            result['symbol_table'] = analyzer.symbol_table.pretty_print()
            result['failed_stage'] = 'none'
        except CompilerError:
            result['symbol_table'] = analyzer.symbol_table.pretty_print()
            result['failed_stage'] = 'semantic'

        return result

    def _send_json(self, data):
        """Send a JSON response."""
        response = json.dumps(data, default=str).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(response))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response)

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        """Custom log format."""
        print(f"[Visualizer] {args[0]}")


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server = HTTPServer(('localhost', port), VisualizerHandler)
    print(f"\n  ╔══════════════════════════════════════════════════╗")
    print(f"  ║   MiniLang Compiler Visualizer                   ║")
    print(f"  ║   Open: http://localhost:{port}                    ║")
    print(f"  ║   Press Ctrl+C to stop                           ║")
    print(f"  ╚══════════════════════════════════════════════════╝\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
        server.server_close()


if __name__ == '__main__':
    main()
