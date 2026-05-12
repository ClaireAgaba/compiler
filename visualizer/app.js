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
}`
};

// ════════════════════════════════════════════════════════════════
// DOM REFERENCES
// ════════════════════════════════════════════════════════════════

const editor = document.getElementById('source-editor');
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

    // UI feedback
    btnCompile.classList.add('compiling');
    btnCompile.innerHTML = '<span class="btn-icon compiling-indicator">⚙</span> Compiling...';
    errorDisplay.style.display = 'none';

    try {
        const response = await fetch('/api/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source })
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
    const keywordTypes = ['FUNC', 'VAR', 'IF', 'ELSE', 'WHILE', 'FOR', 'RETURN',
                          'PRINT', 'INPUT', 'TRUE', 'FALSE', 'AND', 'OR', 'NOT',
                          'INT', 'FLOAT', 'BOOL', 'STRING', 'VOID'];
    const literalTypes = ['INTEGER_LITERAL', 'FLOAT_LITERAL', 'STRING_LITERAL', 'BOOL_LITERAL'];
    const operatorTypes = ['PLUS', 'MINUS', 'STAR', 'SLASH', 'PERCENT', 'EQ', 'NEQ',
                           'LT', 'GT', 'LTE', 'GTE', 'ASSIGN', 'ARROW'];
    const delimiterTypes = ['LPAREN', 'RPAREN', 'LBRACE', 'RBRACE', 'LBRACKET',
                            'RBRACKET', 'SEMICOLON', 'COLON', 'COMMA'];

    function getTokenClass(type) {
        if (keywordTypes.includes(type)) return 'keyword';
        if (literalTypes.includes(type)) return 'literal';
        if (operatorTypes.includes(type)) return 'operator';
        if (delimiterTypes.includes(type)) return 'delimiter';
        if (type === 'IDENTIFIER') return 'identifier';
        return 'special';
    }

    let html = `
        <div class="section-header">
            <span class="section-icon">🔤</span>
            <h3>Stage 1: Lexical Analysis</h3>
        </div>
        <p class="section-desc">The lexer scans source code character-by-character and produces a stream of tokens — the smallest meaningful units of the language.</p>
        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-value">${tokens.length}</div>
                <div class="stat-label">Total Tokens</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${tokens.filter(t => keywordTypes.includes(t.type)).length}</div>
                <div class="stat-label">Keywords</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${tokens.filter(t => t.type === 'IDENTIFIER').length}</div>
                <div class="stat-label">Identifiers</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${tokens.filter(t => literalTypes.includes(t.type)).length}</div>
                <div class="stat-label">Literals</div>
            </div>
        </div>
        <table class="token-table">
            <thead><tr><th>#</th><th>Type</th><th>Value</th><th>Line</th><th>Col</th></tr></thead>
            <tbody>
    `;

    tokens.forEach((token, i) => {
        const cls = getTokenClass(token.type);
        html += `<tr>
            <td style="color: var(--text-muted)">${i + 1}</td>
            <td><span class="token-type ${cls}">${token.type}</span></td>
            <td>${escapeHtml(token.value)}</td>
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
    view.innerHTML = `
        <div class="section-header">
            <span class="section-icon">🌳</span>
            <h3>Stage 2: Parsing (Abstract Syntax Tree)</h3>
        </div>
        <p class="section-desc">The parser reads the token stream using recursive descent (top-down) and builds an Abstract Syntax Tree — a hierarchical representation of the program's structure.</p>
        <div class="code-block">${highlightAST(escapeHtml(ast))}</div>
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
