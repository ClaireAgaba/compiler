/**
 * MiniLang Compiler Visualizer — Frontend Application
 * =====================================================
 * Interactive web app for stepping through compiler stages.
 * Communicates with the Python backend via REST API.
 */

// ════════════════════════════════════════════════════════════════
// EXAMPLE PROGRAMS
// ════════════════════════════════════════════════════════════════

const EXAMPLES = {
    fibonacci: `// Fibonacci Sequence
// Demonstrates: recursion, functions, loops, conditionals

func fibonacci(n: int) -> int {
    if (n <= 1) {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

func main() -> void {
    var limit: int = 10;
    var i: int = 0;

    print("Fibonacci Sequence:");
    while (i < limit) {
        print(fibonacci(i));
        i = i + 1;
    }
}`,

    factorial: `// Factorial Calculator
// Demonstrates: recursion, comparisons, arithmetic

func factorial(n: int) -> int {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

func main() -> void {
    var i: int = 0;
    print("Factorial Table:");
    while (i <= 10) {
        print(factorial(i));
        i = i + 1;
    }
}`,

    calculator: `// Calculator Demo
// Demonstrates: multiple functions, arithmetic, boolean logic

func max(a: int, b: int) -> int {
    if (a > b) {
        return a;
    }
    return b;
}

func power(base: int, exp: int) -> int {
    var result: int = 1;
    var i: int = 0;
    while (i < exp) {
        result = result * base;
        i = i + 1;
    }
    return result;
}

func main() -> void {
    var a: int = 15;
    var b: int = 7;

    print("a + b =");
    print(a + b);

    print("a * b =");
    print(a * b);

    print("max(a, b) =");
    print(max(a, b));

    print("2^10 =");
    print(power(2, 10));
}`,

    simple: `// Simple Demo
// Perfect for walking through each stage

func add(a: int, b: int) -> int {
    return a + b;
}

func main() -> void {
    var x: int = 5;
    var y: int = 3;
    var result: int = add(x, y);
    print("Result:");
    print(result);
}`,

    inputDemo: `// Input Demo
// Type one number into the Runtime Inputs box and compile

func main() -> void {
    var x: int = input();
    print(x * 5 - 2);
}`
};

// ════════════════════════════════════════════════════════════════
// DOM REFERENCES
// ════════════════════════════════════════════════════════════════

const editor = document.getElementById('source-editor');
const runtimeInputs = document.getElementById('runtime-inputs');
const lineNumbers = document.getElementById('line-numbers');
const btnCompile = document.getElementById('btn-compile');
const exampleSelect = document.getElementById('example-select');
const stageContent = document.getElementById('stage-content');
const errorDisplay = document.getElementById('error-display');
const placeholder = document.getElementById('stage-placeholder');
const stageTabs = document.querySelectorAll('.stage-tab');
const pipeStages = document.querySelectorAll('.pipe-stage');

let currentStage = 'tokens';
let compiledData = null;

// ════════════════════════════════════════════════════════════════
// INITIALIZATION
// ════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    // Load default example
    editor.value = EXAMPLES.simple;
    updateLineNumbers();

    // Event listeners
    editor.addEventListener('input', updateLineNumbers);
    editor.addEventListener('scroll', syncScroll);
    editor.addEventListener('keydown', handleTab);
    btnCompile.addEventListener('click', compile);
    exampleSelect.addEventListener('change', loadExample);

    // Stage tab clicks
    stageTabs.forEach(tab => {
        tab.addEventListener('click', () => switchStage(tab.dataset.stage));
    });

    // Pipeline diagram clicks
    pipeStages.forEach(stage => {
        stage.addEventListener('click', () => switchStage(stage.dataset.stage));
    });
});

// ════════════════════════════════════════════════════════════════
// EDITOR FEATURES
// ════════════════════════════════════════════════════════════════

function updateLineNumbers() {
    const lines = editor.value.split('\n');
    lineNumbers.innerHTML = lines.map((_, i) => `<div>${i + 1}</div>`).join('');
}

function syncScroll() {
    lineNumbers.scrollTop = editor.scrollTop;
}

function handleTab(e) {
    if (e.key === 'Tab') {
        e.preventDefault();
        const start = editor.selectionStart;
        const end = editor.selectionEnd;
        editor.value = editor.value.substring(0, start) + '    ' + editor.value.substring(end);
        editor.selectionStart = editor.selectionEnd = start + 4;
        updateLineNumbers();
    }
}

function loadExample() {
    const name = exampleSelect.value;
    if (name && EXAMPLES[name]) {
        editor.value = EXAMPLES[name];
        runtimeInputs.value = name === 'inputDemo' ? '7' : '';
        updateLineNumbers();
        exampleSelect.value = '';
    }
}

// ════════════════════════════════════════════════════════════════
// COMPILATION
// ════════════════════════════════════════════════════════════════

async function compile() {
    const source = editor.value.trim();
    if (!source) return;
    const inputs = runtimeInputs.value
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0);

    // UI feedback
    btnCompile.classList.add('compiling');
    btnCompile.innerHTML = '<span class="btn-icon compiling-indicator">⚙</span> Compiling...';
    errorDisplay.style.display = 'none';

    try {
        const response = await fetch('/api/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source, inputs })
        });

        const data = await response.json();

        if (data.success) {
            compiledData = data;
            placeholder.style.display = 'none';
            renderStage(currentStage);
            updatePipelineHighlight();
        } else {
            showError(data.error, data.error_type);
        }
    } catch (err) {
        showError(`Connection error: ${err.message}\n\nMake sure the server is running:\n  python server.py`, 'NetworkError');
    } finally {
        btnCompile.classList.remove('compiling');
        btnCompile.innerHTML = '<span class="btn-icon">▶</span> Compile & Run';
    }
}

function showError(message, type) {
    errorDisplay.style.display = 'block';
    errorDisplay.innerHTML = `<div class="error-header">❌ ${type || 'Error'}</div>${escapeHtml(message)}`;

    // Hide stage views
    document.querySelectorAll('.stage-view').forEach(v => v.style.display = 'none');
    placeholder.style.display = 'none';
}

// ════════════════════════════════════════════════════════════════
// STAGE SWITCHING
// ════════════════════════════════════════════════════════════════

function switchStage(stage) {
    currentStage = stage;

    // Update tab styling
    stageTabs.forEach(tab => {
        tab.classList.toggle('active', tab.dataset.stage === stage);
    });

    // Update pipeline highlight
    updatePipelineHighlight();

    // Render if data exists
    if (compiledData) {
        renderStage(stage);
    }
}

function updatePipelineHighlight() {
    pipeStages.forEach(stage => {
        stage.classList.toggle('active', stage.dataset.stage === currentStage);
    });
}

// ════════════════════════════════════════════════════════════════
// STAGE RENDERERS
// ════════════════════════════════════════════════════════════════

function renderStage(stage) {
    // Hide all views
    document.querySelectorAll('.stage-view').forEach(v => v.style.display = 'none');
    errorDisplay.style.display = 'none';
    placeholder.style.display = 'none';

    const view = document.getElementById(`stage-${stage}`);
    if (!view || !compiledData) return;

    switch (stage) {
        case 'tokens':   renderTokens(view); break;
        case 'ast':      renderAST(view); break;
        case 'symbols':  renderSymbols(view); break;
        case 'tac':      renderTAC(view); break;
        case 'optimized': renderOptimized(view); break;
        case 'bytecode': renderBytecode(view); break;
        case 'output':   renderOutput(view); break;
    }

    view.style.display = 'block';
}

// ── Stage 1: Tokens ──

function renderTokens(view) {
    const tokens = compiledData.tokens;
    const visibleTokens = tokens.filter(token => token.type !== 'EOF');
    const keywordTypes = ['FUNC', 'VAR', 'IF', 'ELSE', 'WHILE', 'FOR', 'RETURN',
                          'TRUE', 'FALSE', 'AND', 'OR', 'NOT',
                          'INT', 'FLOAT', 'BOOL', 'STRING', 'VOID'];
    const literalTypes = ['INTEGER_LITERAL', 'FLOAT_LITERAL', 'STRING_LITERAL', 'BOOL_LITERAL'];
    const operatorTypes = ['PLUS', 'MINUS', 'STAR', 'SLASH', 'PERCENT', 'EQ', 'NEQ',
                           'LT', 'GT', 'LTE', 'GTE', 'ASSIGN', 'ARROW'];
    const delimiterTypes = ['LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'LBRACKET',
                            'RBRACKET', 'SEMICOLON', 'COLON', 'COMMA'];

    const categoryLabels = {
        keyword: 'Keyword',
        identifier: 'Identifier',
        literal: 'Literal',
        operator: 'Operator',
        delimiter: 'Delimiter',
        special: 'Special'
    };

    const tokenMeanings = {
        LPAREN: 'opening parenthesis',
        RPAREN: 'closing parenthesis',
        LBRACE: 'opening brace',
        RBRACE: 'closing brace',
        LBRACKET: 'opening bracket',
        RBRACKET: 'closing bracket',
        SEMICOLON: 'statement terminator',
        COLON: 'type separator',
        COMMA: 'separator',
        LTE: 'less than or equal',
        GTE: 'greater than or equal',
        LT: 'less than',
        GT: 'greater than',
        EQ: 'equal comparison',
        NEQ: 'not equal comparison',
        ASSIGN: 'assignment',
        ARROW: 'return type arrow'
    };

    const tokenRegexPatterns = {
        // Keywords - matched as exact reserved words
        FUNC: `[a-zA-Z_][a-zA-Z0-9_]*`,
        VAR: `[a-zA-Z_][a-zA-Z0-9_]*`,
        IF: `[a-zA-Z_][a-zA-Z0-9_]*`,
        ELSE: `[a-zA-Z_][a-zA-Z0-9_]*`,
        WHILE: `[a-zA-Z_][a-zA-Z0-9_]*`,
        FOR: `[a-zA-Z_][a-zA-Z0-9_]*`,
        RETURN: `[a-zA-Z_][a-zA-Z0-9_]*`,
        TRUE: `[a-zA-Z_][a-zA-Z0-9_]*`,
        FALSE: `[a-zA-Z_][a-zA-Z0-9_]*`,
        AND: `[a-zA-Z_][a-zA-Z0-9_]*`,
        OR: `[a-zA-Z_][a-zA-Z0-9_]*`,
        NOT: `[a-zA-Z_][a-zA-Z0-9_]*`,
        INT: `[a-zA-Z_][a-zA-Z0-9_]*`,
        FLOAT: `[a-zA-Z_][a-zA-Z0-9_]*`,
        BOOL: `[a-zA-Z_][a-zA-Z0-9_]*`,
        STRING: `[a-zA-Z_][a-zA-Z0-9_]*`,
        VOID: `[a-zA-Z_][a-zA-Z0-9_]*`,
        // Identifiers
        IDENTIFIER: `[a-zA-Z_][a-zA-Z0-9_]*`,
        // Literals
        INTEGER_LITERAL: `[0-9]+`,
        FLOAT_LITERAL: `[0-9]+\\.[0-9]+`,
        STRING_LITERAL: `"([^"\\\\]|\\\\.)*"`,
        BOOL_LITERAL: `true|false`,
        // Operators
        PLUS: `\\+`,
        MINUS: `-`,
        STAR: `\\*`,
        SLASH: `/`,
        PERCENT: `%`,
        EQ: `==`,
        NEQ: `!=`,
        LT: `<`,
        GT: `>`,
        LTE: `<=`,
        GTE: `>=`,
        ASSIGN: `=`,
        ARROW: `->`,
        // Delimiters
        LPAREN: `\\(`,
        RPAREN: `\\)`,
        LBRACE: `\\{`,
        RBRACE: `\\}`,
        LBRACKET: `\\[`,
        RBRACKET: `\\]`,
        SEMICOLON: `;`,
        COLON: `:`,
        COMMA: `,`
    };

    function getTokenClass(type) {
        if (keywordTypes.includes(type)) return 'keyword';
        if (literalTypes.includes(type)) return 'literal';
        if (operatorTypes.includes(type)) return 'operator';
        if (delimiterTypes.includes(type)) return 'delimiter';
        if (type === 'IDENTIFIER') return 'identifier';
        return 'special';
    }

    function formatTypeName(type) {
        return type.replace(/_/g, ' ').toLowerCase();
    }

    function getTokenRegex(type) {
        return tokenRegexPatterns[type] || '(custom)';
    }

    let html = `
        <div class="section-header">
            <span class="section-icon">🔤</span>
            <h3>Stage 1: Lexical Analysis</h3>
        </div>
        <p class="section-desc">The lexer scans source code character-by-character and produces a stream of tokens. Every token belongs to one of five groups: keyword, identifier, literal, operator, or delimiter.</p>
        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-value">${visibleTokens.length}</div>
                <div class="stat-label">Visible Tokens</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${visibleTokens.filter(t => keywordTypes.includes(t.type)).length}</div>
                <div class="stat-label">Keywords</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${visibleTokens.filter(t => t.type === 'IDENTIFIER').length}</div>
                <div class="stat-label">Identifiers</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${visibleTokens.filter(t => literalTypes.includes(t.type)).length}</div>
                <div class="stat-label">Literals</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${visibleTokens.filter(t => operatorTypes.includes(t.type)).length}</div>
                <div class="stat-label">Operators</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${visibleTokens.filter(t => delimiterTypes.includes(t.type)).length}</div>
                <div class="stat-label">Delimiters</div>
            </div>
        </div>
        <div class="token-legend">
            <div class="legend-item"><span class="token-type keyword">Keyword</span><span>Reserved words such as func, if, while, int</span></div>
            <div class="legend-item"><span class="token-type identifier">Identifier</span><span>User-defined names such as add, a, result</span></div>
            <div class="legend-item"><span class="token-type literal">Literal</span><span>Constant values such as 5, 3.14, true, "hello"</span></div>
            <div class="legend-item"><span class="token-type operator">Operator</span><span>Symbols that compute or compare, such as +, =, &lt;=, -&gt;</span></div>
            <div class="legend-item"><span class="token-type delimiter">Delimiter</span><span>Structure symbols such as ( ) { } ; , :</span></div>
        </div>
        <p class="token-note">Compiler-specific names like LPAREN and LTE are just precise internal labels. LPAREN means "(" and belongs to the Delimiter category. LTE means "&lt;=" and belongs to the Operator category. The <strong>Regex Pattern</strong> column shows the formal language pattern that matches this token type.</p>
        <table class="token-table">
            <thead><tr><th>#</th><th>Compiler Token</th><th>Class Category</th><th>Value</th><th>Regex Pattern</th><th>Meaning</th><th>Line</th><th>Col</th></tr></thead>
            <tbody>
    `;

    visibleTokens.forEach((token, i) => {
        const cls = getTokenClass(token.type);
        const category = categoryLabels[cls] || 'Special';
        const meaning = tokenMeanings[token.type] || formatTypeName(token.type);
        const regex = getTokenRegex(token.type);
        html += `<tr>
            <td style="color: var(--text-muted)">${i + 1}</td>
            <td><span class="token-type ${cls}">${token.type}</span></td>
            <td>${category}</td>
            <td>${escapeHtml(token.value)}</td>
            <td style="color: var(--text-primary); font-family: monospace; font-size: 0.75rem; background: rgba(255,255,255,0.03); padding: 2px 4px; border-radius: 2px;">${escapeHtml(regex)}</td>
            <td style="color: var(--text-secondary)">${escapeHtml(meaning)}</td>
            <td style="color: var(--text-muted)">${token.line}</td>
            <td style="color: var(--text-muted)">${token.column}</td>
        </tr>`;
    });

    html += '</tbody></table>';
    view.innerHTML = html;
}

// ── Stage 2: AST ──

function renderAST(view) {
    const ast = compiledData.ast;
    const metadata = compiledData.parsing_metadata || {};
    const strategy = metadata.strategy || 'Top-Down Recursive Descent (LL(1))';
    const grammarRules = metadata.grammar_rules || [];
    const maxDepth = metadata.max_recursion_depth || 0;
    const productionRules = [
        { lhs: 'program', rhs: 'function* EOF', impl: 'parse()' },
        { lhs: 'function', rhs: '"func" IDENT "(" params? ")" "->" type block', impl: '_parse_function()' },
        { lhs: 'params', rhs: 'param ("," param)* | epsilon', impl: '_parse_params()' },
        { lhs: 'param', rhs: 'IDENT ":" type', impl: '_parse_param()' },
        { lhs: 'type', rhs: '"int" | "float" | "bool" | "string" | "void" | type "[" INT "]"', impl: '_parse_type()' },
        { lhs: 'block', rhs: '"{" statement* "}"', impl: '_parse_block()' },
        { lhs: 'statement', rhs: 'var_decl | if_stmt | while_stmt | for_stmt | return_stmt | print_stmt | assignment | expr_stmt', impl: '_parse_statement()' },
        { lhs: 'var_decl', rhs: '"var" IDENT ":" type ("=" expr)? ";"', impl: '_parse_var_decl()' },
        { lhs: 'if_stmt', rhs: '"if" "(" expr ")" block ("else" ("if" ... | block))?', impl: '_parse_if()' },
        { lhs: 'while_stmt', rhs: '"while" "(" expr ")" block', impl: '_parse_while()' },
        { lhs: 'for_stmt', rhs: '"for" "(" (var_decl | ";") expr? ";" assignment? ")" block', impl: '_parse_for()' },
        { lhs: 'return_stmt', rhs: '"return" expr? ";"', impl: '_parse_return()' },
        { lhs: 'print_stmt', rhs: '"print" "(" expr ")" ";"', impl: '_parse_print()' },
        { lhs: 'expr', rhs: 'or_expr', impl: '_parse_expression()' },
        { lhs: 'or_expr', rhs: 'and_expr ("or" and_expr)*', impl: '_parse_or()' },
        { lhs: 'and_expr', rhs: 'equality ("and" equality)*', impl: '_parse_and()' },
        { lhs: 'equality', rhs: 'comparison (("==" | "!=") comparison)*', impl: '_parse_equality()' },
        { lhs: 'comparison', rhs: 'term (("<" | ">" | "<=" | ">=") term)*', impl: '_parse_comparison()' },
        { lhs: 'term', rhs: 'factor (("+" | "-") factor)*', impl: '_parse_term()' },
        { lhs: 'factor', rhs: 'unary (("*" | "/" | "%") unary)*', impl: '_parse_factor()' },
        { lhs: 'unary', rhs: '("not" | "-") unary | primary', impl: '_parse_unary()' },
        { lhs: 'primary', rhs: 'NUMBER | STRING | BOOL | IDENT | "(" expr ")" | input_call', impl: '_parse_primary()' }
    ];

    const firstFollowRows = [
        {
            nt: 'program',
            first: '{ func }',
            follow: '{ EOF }'
        },
        {
            nt: 'function',
            first: '{ func }',
            follow: '{ func, EOF }'
        },
        {
            nt: 'statement',
            first: '{ var, if, while, for, return, IDENT, (, -, not, INT_LIT, FLOAT_LIT, STRING_LIT, true, false }',
            follow: '{ var, if, while, for, return, IDENT, }, EOF }'
        },
        {
            nt: 'expr',
            first: '{ IDENT, (, -, not, INT_LIT, FLOAT_LIT, STRING_LIT, true, false }',
            follow: '{ ;, ), ], , }'
        },
        {
            nt: 'term',
            first: '{ IDENT, (, -, not, INT_LIT, FLOAT_LIT, STRING_LIT, true, false }',
            follow: '{ +, -, <, >, <=, >=, ==, !=, and, or, ;, ), ], , }'
        },
        {
            nt: 'factor',
            first: '{ IDENT, (, -, not, INT_LIT, FLOAT_LIT, STRING_LIT, true, false }',
            follow: '{ *, /, %, +, -, <, >, <=, >=, ==, !=, and, or, ;, ), ], , }'
        }
    ];


    // Runtime grammar rules applied (for this specific input)
    let rulesHtml = '<div class="parser-table-wrap">';
    rulesHtml += '<table class="parser-table">';
    rulesHtml += '<thead><tr>';
    rulesHtml += '<th>Rule</th>';
    rulesHtml += '<th>Production</th>';
    rulesHtml += '<th>Token</th>';
    rulesHtml += '<th>Depth</th>';
    rulesHtml += '</tr></thead><tbody>';

    grammarRules.forEach((rule, i) => {
        const ruleShort = rule.rule.replace('_parse_', '');
        rulesHtml += `<tr>
            <td><span class="parser-pill">${escapeHtml(ruleShort)}</span></td>
            <td><span class="parser-subtle">${escapeHtml(rule.production)}</span></td>
            <td><span class="parser-subtle">'${escapeHtml(rule.token)}'</span></td>
            <td><span class="parser-subtle">${rule.depth}</span></td>
        </tr>`;
    });

    rulesHtml += '</tbody></table></div>';

    // Static production rules + implementation mapping
    let productionHtml = '<div class="parser-table-wrap">';
    productionHtml += '<table class="parser-table">';
    productionHtml += '<thead><tr>';
    productionHtml += '<th>Production</th>';
    productionHtml += '<th>Implemented In</th>';
    productionHtml += '</tr></thead><tbody>';

    productionRules.forEach((p, i) => {
        productionHtml += `<tr>
            <td><span class="parser-nt">${escapeHtml(p.lhs)}</span> -> <span class="parser-subtle">${escapeHtml(p.rhs)}</span></td>
            <td><span class="parser-pill">${escapeHtml(p.impl)}</span></td>
        </tr>`;
    });

    productionHtml += '</tbody></table></div>';

    let firstFollowHtml = '<div class="parser-table-wrap">';
    firstFollowHtml += '<table class="parser-table">';
    firstFollowHtml += '<thead><tr>';
    firstFollowHtml += '<th>Non-terminal</th>';
    firstFollowHtml += '<th>FIRST</th>';
    firstFollowHtml += '<th>FOLLOW</th>';
    firstFollowHtml += '</tr></thead><tbody>';

    firstFollowRows.forEach((row, i) => {
        firstFollowHtml += `<tr>
            <td><span class="parser-pill">${escapeHtml(row.nt)}</span></td>
            <td><span class="parser-subtle">${escapeHtml(row.first)}</span></td>
            <td><span class="parser-subtle">${escapeHtml(row.follow)}</span></td>
        </tr>`;
    });

    firstFollowHtml += '</tbody></table></div>';

    const parseTreeText = [
        'Expression: a + b * c',
        '',
        'Parse Tree (Grammar-Oriented)',
        'expr',
        '├── term',
        '│   └── IDENT(a)',
        '├── PLUS(+)',
        '└── term',
        '    ├── factor',
        '    │   └── IDENT(b)',
        '    ├── STAR(*)',
        '    └── factor',
        '        └── IDENT(c)'
    ].join('\n');

    const astTreeText = [
        'Expression: a + b * c',
        '',
        'AST (Semantics-Oriented)',
        'BinaryOp(+)',
        '├── Identifier(a)',
        '└── BinaryOp(*)',
        '    ├── Identifier(b)',
        '    └── Identifier(c)'
    ].join('\n');

    const parseTreeAstHtml = `
        <div class="parser-compare-grid">
            <div class="parser-compare-card">
                <h5 class="parser-compare-title">Parse Tree</h5>
                <p class="parser-compare-note">Shows all grammar symbols and intermediate non-terminals exactly as expanded by productions.</p>
                <div class="code-block parser-mini-block">${escapeHtml(parseTreeText)}</div>
            </div>
            <div class="parser-compare-card">
                <h5 class="parser-compare-title">Abstract Syntax Tree (AST)</h5>
                <p class="parser-compare-note">Compresses syntax and keeps only the essential semantic structure used by later compiler stages.</p>
                <div class="code-block parser-mini-block">${escapeHtml(astTreeText)}</div>
            </div>
        </div>
    `;

    // Parser strategy section
    let strategyHtml = `
        <div class="parser-callout">
            <h4>Parser Strategy</h4>
            <p>
                <strong>Method:</strong> ${escapeHtml(strategy)}<br/>
                <strong>Direction:</strong> Top-down (start from root, work toward leaves)<br/>
                <strong>Lookahead:</strong> LL(1) — one token lookahead for decision making<br/>
                <strong>Approach:</strong> Recursive descent — each grammar rule is a parser function<br/>
                <strong>Grammar Complexity:</strong> ${grammarRules.length} rules applied, max recursion depth: ${maxDepth}
            </p>
        </div>
    `;

    view.innerHTML = `
        <div class="section-header">
            <span class="section-icon">🌳</span>
            <h3>Stage 2: Parsing (Syntax Analysis)</h3>
        </div>
        <p class="section-desc">The parser reads the token stream and builds an Abstract Syntax Tree (AST) — a hierarchical representation of the program's structure. It uses a <strong>top-down recursive descent</strong> strategy with <strong>LL(1)</strong> lookahead to predictively parse the tokens.</p>
        
        ${strategyHtml}

        <div class="parser-section">
            <h4 class="parser-section-title">Grammar Rules Applied for This Program (${grammarRules.length} total)</h4>
            ${rulesHtml}
        </div>

        <div class="parser-section">
            <h4 class="parser-section-title">Production Rules and Implementation Mapping</h4>
            <p class="parser-section-note">Each grammar production from syntax analysis is implemented by a recursive parser method in our code.</p>
            ${productionHtml}
        </div>

        <div class="parser-section">
            <h4 class="parser-section-title">FIRST and FOLLOW Sets (LL(1) Preparation)</h4>
            <p class="parser-section-note">These sets are used to construct a table-driven predictive parser. They show which tokens can start a non-terminal (FIRST) and which tokens can appear after it (FOLLOW).</p>
            ${firstFollowHtml}
        </div>

        <div class="parser-section">
            <h4 class="parser-section-title">Parse Tree vs AST Comparison</h4>
            <p class="parser-section-note">Both structures represent the same expression, but they serve different purposes in syntax analysis and compilation.</p>
            ${parseTreeAstHtml}
        </div>

        <div style="margin-bottom: 16px;">
            <h4 style="margin-bottom: 8px; color: var(--text-secondary); font-size: 0.9rem;">Abstract Syntax Tree</h4>
            <div class="code-block">${highlightAST(escapeHtml(ast))}</div>
        </div>
    `;
}

// ── Stage 3: Semantic Analysis ──

function renderSymbols(view) {
    const table = compiledData.symbol_table;
    view.innerHTML = `
        <div class="section-header">
            <span class="section-icon">🔍</span>
            <h3>Stage 3: Semantic Analysis</h3>
        </div>
        <p class="section-desc">The semantic analyzer walks the AST, builds a symbol table, checks types, resolves names, and ensures the program is meaningful — not just syntactically correct.</p>
        <div class="code-block">${highlightSymbols(escapeHtml(table))}</div>
    `;
}

// ── Stage 4: Three-Address Code ──

function renderTAC(view) {
    const tac = compiledData.tac;
    view.innerHTML = `
        <div class="section-header">
            <span class="section-icon">📋</span>
            <h3>Stage 4: Intermediate Code Generation (TAC)</h3>
        </div>
        <p class="section-desc">Three-Address Code is a linear intermediate representation where each instruction has at most three operands. This bridges the gap between the high-level AST and low-level bytecode.</p>
        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-value">${tac.length}</div>
                <div class="stat-label">TAC Instructions</div>
            </div>
        </div>
        <div class="code-block">${highlightTAC(tac.map(escapeHtml).join('\n'))}</div>
    `;
}

// ── Stage 5: Optimizer ──

function renderOptimized(view) {
    const optimized = compiledData.optimized_tac;
    const report = compiledData.optimization_report;
    const tac = compiledData.tac;

    let reportHtml = report.map(r => {
        const icon = r.includes('0 ') ? '⚪' : '✅';
        return `<div class="opt-item"><span class="opt-icon">${icon}</span>${escapeHtml(r)}</div>`;
    }).join('');

    view.innerHTML = `
        <div class="section-header">
            <span class="section-icon">⚡</span>
            <h3>Stage 5: Code Optimization</h3>
        </div>
        <p class="section-desc">The optimizer applies multiple passes to improve the TAC: constant folding, constant propagation, dead code elimination, common subexpression elimination, and strength reduction.</p>
        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-value">${tac.length}</div>
                <div class="stat-label">Before</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${optimized.length}</div>
                <div class="stat-label">After</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${tac.length > 0 ? Math.round((1 - optimized.length / tac.length) * 100) : 0}%</div>
                <div class="stat-label">Reduction</div>
            </div>
        </div>
        <h4 style="margin-bottom:8px; color: var(--text-secondary); font-size: 0.8rem;">Optimization Report</h4>
        ${reportHtml}
        <h4 style="margin: 16px 0 8px; color: var(--text-secondary); font-size: 0.8rem;">Optimized TAC</h4>
        <div class="code-block">${highlightTAC(optimized.map(escapeHtml).join('\n'))}</div>
    `;
}

// ── Stage 6: Bytecode ──

function renderBytecode(view) {
    const bytecode = compiledData.bytecode;
    const functions = compiledData.functions;

    let funcInfo = Object.entries(functions).map(([name, addr]) =>
        `<div class="stat-card"><div class="stat-value">${name}()</div><div class="stat-label">Address: ${addr}</div></div>`
    ).join('');

    let rows = bytecode.map(b => {
        const parts = b.instruction.split(' ');
        const opcode = parts[0] || '';
        const operand = parts.slice(1).join(' ');
        return `<tr>
            <td class="addr">${String(b.index).padStart(4, '0')}</td>
            <td class="opcode">${escapeHtml(opcode)}</td>
            <td class="operand">${escapeHtml(operand)}</td>
        </tr>`;
    }).join('');

    view.innerHTML = `
        <div class="section-header">
            <span class="section-icon">💾</span>
            <h3>Stage 6: Code Generation (Bytecode)</h3>
        </div>
        <p class="section-desc">The code generator translates optimized TAC into bytecode for our stack-based virtual machine. Each instruction operates on an operand stack.</p>
        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-value">${bytecode.length}</div>
                <div class="stat-label">Bytecode Instructions</div>
            </div>
            ${funcInfo}
        </div>
        <table class="bytecode-table">
            <thead><tr><th>Addr</th><th>Opcode</th><th>Operand</th></tr></thead>
            <tbody>${rows}</tbody>
        </table>
    `;
}

// ── Stage 7: Output ──

function renderOutput(view) {
    const output = compiledData.output || [];
    const trace = compiledData.trace || [];
    const steps = compiledData.steps || 0;

    let outputHtml = output.length > 0
        ? output.map(line => `<div class="output-line">${escapeHtml(String(line))}</div>`).join('')
        : '<div style="color: var(--text-muted); font-style: italic;">No output produced</div>';

    let traceHtml = trace.slice(-30).map(line =>
        `<div style="font-size: 0.7rem; color: var(--text-secondary); padding: 1px 0;">${escapeHtml(line)}</div>`
    ).join('');

    view.innerHTML = `
        <div class="section-header">
            <span class="section-icon">🖥️</span>
            <h3>Stage 7: VM Execution (Runtime Environment)</h3>
        </div>
        <p class="section-desc">The stack-based Virtual Machine executes the bytecode. It maintains an operand stack for computation, a call stack for function calls, and a heap for arrays.</p>
        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-value">${steps}</div>
                <div class="stat-label">Execution Steps</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${output.length}</div>
                <div class="stat-label">Output Lines</div>
            </div>
        </div>
        <h4 style="margin-bottom:8px; color: var(--text-secondary); font-size: 0.8rem;">Program Output</h4>
        <div class="code-block" style="border-color: var(--accent-green); background: rgba(63, 185, 80, 0.05);">${outputHtml}</div>
        ${trace.length > 0 ? `
            <h4 style="margin: 16px 0 8px; color: var(--text-secondary); font-size: 0.8rem;">Execution Trace (last 30 steps)</h4>
            <div class="code-block">${traceHtml}</div>
        ` : ''}
    `;
}

// ════════════════════════════════════════════════════════════════
// SYNTAX HIGHLIGHTING HELPERS
// ════════════════════════════════════════════════════════════════

function highlightAST(text) {
    return text
        .replace(/\b(Program|Function|Block|If|While|For|Return|Print|Assign|VarDecl|ExprStmt)\b/g, '<span class="keyword">$1</span>')
        .replace(/\b(BinaryOp|UnaryOp|FunctionCall|ArrayAccess|Input)\b/g, '<span class="function">$1</span>')
        .replace(/\b(Number|String|Bool|Identifier|Param)\b/g, '<span class="function">$1</span>')
        .replace(/\b(int|float|bool|string|void)\b/g, '<span class="number">$1</span>');
}

function highlightSymbols(text) {
    return text
        .replace(/\b(Symbol|Global|Scope Level \d+)\b/g, '<span class="keyword">$1</span>')
        .replace(/\b(variable|parameter|function)\b/g, '<span class="function">$1</span>')
        .replace(/\b(int|float|bool|string|void)\b/g, '<span class="number">$1</span>');
}

function highlightTAC(text) {
    return text
        .replace(/^(\s*)(FUNC_BEGIN|FUNC_END|GOTO|IF_FALSE|IF_TRUE|RETURN|PRINT|CALL|PARAM|INPUT|ARRAY_ALLOC|ARRAY_LOAD|ARRAY_STORE|ASSIGN|LABEL|NEG|NOT)/gm,
            '$1<span class="keyword">$2</span>')
        .replace(/^(L\d+:)/gm, '<span class="label">$1</span>')
        .replace(/\b(t\d+)\b/g, '<span class="function">$1</span>');
}

// ════════════════════════════════════════════════════════════════
// UTILITIES
// ════════════════════════════════════════════════════════════════

function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
