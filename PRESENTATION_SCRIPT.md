# MiniLang Compiler — Presentation Script
## 5 Presenters | ~25-30 minutes total

---

# 🎯 OVERVIEW & SPEAKER ASSIGNMENTS

| Speaker | Section | Time | Topics |
|---------|---------|------|--------|
| **Speaker 1** | Introduction & Lexer | ~5 min | What is a compiler, MiniLang overview, Stage 1: Lexical Analysis |
| **Speaker 2** | Parser & AST | ~5 min | Stage 2: Parsing (Top-Down Recursive Descent), Parse Trees, AST |
| **Speaker 3** | Semantic Analysis | ~5 min | Stage 3: Symbol Table, Type Checking, Scope Resolution |
| **Speaker 4** | IR, Optimization & Code Gen | ~6 min | Stage 4: Three-Address Code, Stage 5: Optimization, Stage 6: Bytecode |
| **Speaker 5** | VM Runtime & Live Demo | ~6 min | Stage 7: Virtual Machine, Live Demo on Visualizer, Conclusion |

---
---

# SPEAKER 1: Introduction & Lexical Analysis (~5 min)

---

## SLIDE: Title Slide

> Good morning/afternoon everyone. Today we are going to present our compiler design project. We designed and built a complete compiler from scratch in Python for a custom programming language we call **MiniLang**. Our compiler covers all seven stages of compilation — from lexical analysis all the way to a runtime environment — and we built everything by hand, no external libraries like PLY or ANTLR. Everything is hand-written to demonstrate that we truly understand how each stage works.

---

## SLIDE: What is a Compiler?

> So, before we dive in, let us quickly recap — what is a compiler? A compiler is a program that translates source code written in a high-level programming language into a lower-level representation that a machine can execute. It does this through a series of well-defined stages, often grouped into three parts:
>
> The **Front End**, which handles understanding the source code — that is lexical analysis, parsing, and semantic analysis.
>
> The **Middle End**, which generates and optimizes an intermediate representation.
>
> And the **Back End**, which generates the final target code and handles execution.
>
> Our compiler implements all of these. Let me walk you through the architecture.

---

## SLIDE: Compiler Architecture Diagram

> Here is the architecture of our compiler. Source code written in MiniLang flows through seven stages:
>
> First, the **Lexer** scans the source code and produces a stream of tokens. These tokens are fed into the **Parser**, which builds an Abstract Syntax Tree. The **Semantic Analyzer** then checks the AST for type errors and builds a symbol table. Next, the **Intermediate Code Generator** converts the AST into Three-Address Code. The **Optimizer** applies several optimization passes. The **Code Generator** translates the optimized code into bytecode. And finally, our **Virtual Machine** executes that bytecode and produces the output.
>
> Each of these stages is implemented as a separate Python module, making the design clean and modular.

---

## SLIDE: The MiniLang Language

> Now let me briefly introduce the language we are compiling. MiniLang is a simple but expressive C-like language. It supports:
>
> - Five data types: `int`, `float`, `bool`, `string`, and `void`
> - Variable declarations with explicit types, like `var x: int = 5;`
> - Functions with typed parameters and return types
> - Control flow: `if/else`, `while` loops, and `for` loops
> - Arithmetic, comparison, and logical operators
> - Arrays with index-based access
> - Built-in `print` and `input` for I/O
> - Single-line and multi-line comments
>
> Here is a quick example — a Fibonacci function. You can see the syntax is quite familiar if you know C or JavaScript.

---

## SLIDE: Stage 1 — Lexical Analysis (The Lexer)

> Now let us start with Stage 1 — Lexical Analysis. The lexer, also called the scanner, is the first phase of the compiler. Its job is to read the raw source code **character by character** and group those characters into meaningful units called **tokens**.
>
> A token is the smallest meaningful element in the language. For example, the keyword `func`, an identifier like `fibonacci`, an operator like `+`, or a number like `42` — each of these is a single token.
>
> Our lexer is **hand-written** — it does not use regular expressions or any external tools. It is a character-by-character scanner that processes the source code from left to right.

---

## SLIDE: How the Lexer Works

> The lexer works as follows:
>
> First, it **skips whitespace and comments** — these are not meaningful to the compiler.
>
> Then, when it encounters a letter or underscore, it reads an **identifier or keyword**. It checks the word against a keyword table — if the word is `func`, `var`, `if`, `while`, and so on, it produces a keyword token. Otherwise, it produces an identifier token.
>
> When it encounters a digit, it reads a **number literal** — either an integer or a float if there is a decimal point.
>
> When it encounters a double quote, it reads a **string literal**, handling escape sequences like `\n` and `\t`.
>
> And when it encounters special characters, it recognizes **operators and delimiters**. It also handles multi-character operators like `==`, `!=`, `<=`, `>=`, and the arrow `->`.
>
> Every token stores its **line number and column number**, which is crucial for error reporting in later stages.

---

## SLIDE: Lexer Output Example

> Here is an example. If we feed the source code `var x: int = 5;` into our lexer, it produces the following token stream:
>
> | Token Type | Value | Line | Column |
> |---|---|---|---|
> | VAR | "var" | 1 | 1 |
> | IDENTIFIER | "x" | 1 | 5 |
> | COLON | ":" | 1 | 6 |
> | INT | "int" | 1 | 8 |
> | ASSIGN | "=" | 1 | 12 |
> | INTEGER_LITERAL | 5 | 1 | 14 |
> | SEMICOLON | ";" | 1 | 15 |
>
> Each token has a type, a value, and a source location. This token stream is what gets passed to the next stage — the parser. And with that, I will hand over to [Speaker 2] who will talk about parsing.

---
---

# SPEAKER 2: Parsing & Abstract Syntax Trees (~5 min)

---

## SLIDE: Stage 2 — Parsing

> Thank you, [Speaker 1]. So now we have a flat stream of tokens from the lexer. The problem is — tokens alone do not tell us the **structure** of the program. Is `x + y * z` meant to be `(x + y) * z` or `x + (y * z)`? That is where the **parser** comes in.
>
> The parser's job is to read the token stream and determine the **grammatical structure** of the program according to a set of grammar rules. It produces a tree representation of the program called an **Abstract Syntax Tree**, or AST.

---

## SLIDE: Top-Down vs Bottom-Up Parsing

> There are two main approaches to parsing:
>
> **Top-Down Parsing** starts from the root of the parse tree — the start symbol — and works its way down to the leaves, trying to match the input. The most common form is **Recursive Descent**, which is what we implemented. It is also known as an LL parser because it reads input Left-to-right and produces a Leftmost derivation. Each grammar rule becomes a function in our code — for example, we have `_parse_expression()`, `_parse_if()`, `_parse_while()`, and so on.
>
> **Bottom-Up Parsing** works the other way — it starts from the input tokens and tries to reduce them back to the start symbol. LR parsers and SLR parsers fall into this category. They are more powerful but also more complex to implement by hand.
>
> We chose **Recursive Descent** — top-down parsing — because it is intuitive, easy to implement by hand, and maps directly to the grammar rules. Each grammar rule is literally a function in our parser.

---

## SLIDE: Our Grammar (BNF)

> Here is a portion of our grammar written in BNF notation. For example:
>
> A **program** is zero or more function declarations followed by EOF.
>
> A **function** is the keyword `func`, followed by an identifier, parameters in parentheses, an arrow, a return type, and then a block.
>
> For **expressions**, we handle operator precedence through the grammar structure itself. The lowest precedence operators like `or` are at the top, and the highest precedence operators are at the bottom. This way, multiplication binds tighter than addition, and comparison binds tighter than logical operators — all naturally encoded in the grammar, without needing a separate precedence table.

---

## SLIDE: Parse Trees vs Abstract Syntax Trees

> Now, there is an important distinction between a **Parse Tree** and an **Abstract Syntax Tree**.
>
> A **Parse Tree**, also called a Concrete Syntax Tree, includes every grammar symbol — including punctuation like parentheses, semicolons, and braces. It is a direct representation of the derivation.
>
> An **Abstract Syntax Tree** is a simplified version. It removes unnecessary syntax elements — we do not need semicolons or parentheses in the tree because the tree structure itself encodes the grouping. For example, for the expression `a + b * c`, the AST would have `*` as a child of `+`, showing that multiplication happens first — we do not need the parentheses to know that.
>
> Our parser produces an AST, not a parse tree, because the AST is more practical for the later stages of compilation.

---

## SLIDE: AST Output Example

> Here is what the AST looks like for a simple program. You can see it is a tree structure:
>
> At the top we have a **Program** node containing **Function** nodes. Each function has parameters, a return type, and a body. The body contains statements like **VarDecl**, **If**, **While**, **Return**, and **Print**. Expressions are represented as **BinaryOp** nodes with left and right children.
>
> Each node in our AST also stores the source line and column, so if a later stage finds an error — like a type mismatch — it can report exactly where in the source code the problem is.
>
> Now I will hand over to [Speaker 3] who will explain what happens after we have the AST — semantic analysis.

---
---

# SPEAKER 3: Semantic Analysis (~5 min)

---

## SLIDE: Stage 3 — Semantic Analysis

> Thank you, [Speaker 2]. So at this point we have an AST that represents the structure of the program. But just because a program is syntactically correct does not mean it is meaningful. For example, you could write `"hello" + true` — the parser would accept this because it follows the grammar, but it makes no semantic sense.
>
> This is where **Semantic Analysis** comes in. The semantic analyzer walks the AST and checks whether the program actually **makes sense**. It performs several crucial checks.

---

## SLIDE: What Semantic Analysis Does

> Our semantic analyzer performs the following:
>
> **First, Name Resolution.** Every variable and function must be declared before it is used. If you write `print(x)` but never declared `x`, the semantic analyzer catches that and reports: "Undefined variable: x."
>
> **Second, Type Checking.** Every operation must be type-compatible. You cannot add an integer and a boolean. You cannot assign a string to an integer variable. If a function expects an `int` parameter, you cannot pass a `string`. Our analyzer checks all of these.
>
> **Third, Type Inference.** For every expression, the analyzer determines the result type bottom-up. If you add two integers, the result is an integer. If you divide, the result is a float. If you compare two values, the result is a boolean.
>
> **Fourth, Function Validation.** The analyzer checks that function calls have the correct number of arguments, that each argument type matches the parameter type, and that the return type matches what the function signature promises.
>
> **Fifth, Scope Checking.** Variables declared inside an `if` block or `while` loop are only visible within that block. Our analyzer enforces this.
>
> And **Sixth**, it ensures that a `main()` function exists, since that is the entry point of every MiniLang program.

---

## SLIDE: The Symbol Table

> To perform all these checks, the semantic analyzer uses a data structure called the **Symbol Table**. Our symbol table is implemented as a **stack of hash maps**.
>
> Each hash map represents one **scope level**. The bottom of the stack is the **global scope** — it contains function declarations. When we enter a function body, we push a new scope. When we enter a block like an `if` or `while`, we push another scope. When we exit a block, we pop the scope.
>
> **Lookup** works from the innermost scope outward — if a variable is not found in the current scope, we check the parent scope, then the grandparent, and so on. This is called **lexical scoping** or **static scoping**.
>
> Each entry in the symbol table is a **Symbol** object containing the name, type, kind (whether it is a variable, parameter, or function), the scope level, and for functions, the parameter types and return type.

---

## SLIDE: Semantic Analysis Example

> Let me show you a quick example. Given this code:
>
> ```
> func main() -> void {
>     var x: int = 5;
>     var y: int = x + 3;
>     print(y);
> }
> ```
>
> The semantic analyzer would:
> 1. Register `main` as a function in the global scope
> 2. Enter the function scope
> 3. Register `x` as an integer variable, verify the initializer `5` is also an integer — types match ✓
> 4. Register `y` as an integer variable, analyze `x + 3` — `x` is `int`, `3` is `int`, so `int + int = int` — matches the declared type ✓
> 5. Verify `print(y)` — `y` exists and is defined ✓
> 6. After all checks pass, the AST nodes are **annotated** with their resolved types. This annotated AST is what gets passed to the next stage.
>
> Now I will hand over to [Speaker 4] who will cover the middle end and back end — intermediate code generation, optimization, and code generation.

---
---

# SPEAKER 4: IR Generation, Optimization & Code Generation (~6 min)

---

## SLIDE: Stage 4 — Intermediate Code Generation

> Thank you, [Speaker 3]. So now we have a semantically validated, type-annotated AST. The next step is to convert this tree into a **linear intermediate representation** that is easier to optimize and translate to machine code.
>
> We use **Three-Address Code**, commonly abbreviated as **TAC**. In TAC, each instruction has at most **three operands** — two source operands and one destination. This is a standard intermediate representation used in real compilers like GCC.

---

## SLIDE: Three-Address Code Examples

> Let me show you how source code becomes TAC. Take the expression `x = (a + b) * c`. The TAC would be:
>
> ```
> t0 = a + b
> t1 = t0 * c
> x = t1
> ```
>
> Each complex expression is broken down into simple three-operand instructions using **temporary variables** — `t0`, `t1`, `t2`, and so on. The IR generator creates these automatically.
>
> For control flow, we use **labels** and **jumps**. An `if` statement becomes:
>
> ```
> IF_FALSE condition GOTO L_else
> ... then block ...
> GOTO L_end
> L_else:
> ... else block ...
> L_end:
> ```
>
> And a `while` loop becomes:
>
> ```
> L_start:
> IF_FALSE condition GOTO L_end
> ... body ...
> GOTO L_start
> L_end:
> ```
>
> Function calls use `PARAM` instructions to pass arguments, followed by a `CALL` instruction. This linear format makes optimization much easier than working on the tree directly.

---

## SLIDE: Stage 5 — Code Optimization

> Now we come to one of the most interesting stages — **optimization**. The optimizer takes the TAC and applies multiple passes to make it more efficient. Our optimizer implements five standard optimization techniques:
>
> **1. Constant Folding** — If both operands of an operation are constants, we compute the result at compile time. For example, `t0 = 3 + 5` becomes `t0 = 8`. Why compute it at runtime when we already know the answer?
>
> **2. Constant Propagation** — If we know that `x = 5`, then wherever `x` is used later, we can substitute `5` directly. This often enables further constant folding.
>
> **3. Dead Code Elimination** — If a temporary variable is computed but never used by any later instruction, we remove it entirely. There is no point computing something nobody reads.
>
> **4. Common Subexpression Elimination** — If the expression `a + b` is computed multiple times, we compute it once and reuse the result.
>
> **5. Strength Reduction** — We replace expensive operations with cheaper ones. For example, `x * 2` becomes `x + x`, which is faster. And `x * 0` becomes simply `0`.
>
> Each pass reports what it changed, so we can verify the optimizer is actually improving the code.

---

## SLIDE: Stage 6 — Code Generation (Bytecode)

> After optimization, we need to translate the optimized TAC into code that can actually be executed. Our code generator produces **bytecode** for a custom stack-based virtual machine.
>
> Stack-based bytecode works by pushing operands onto a stack, performing operations that pop operands and push results. For example, to compute `a + b`:
>
> ```
> LOAD a       ← push value of a onto stack
> LOAD b       ← push value of b onto stack
> ADD          ← pop both, push sum
> STORE result ← pop and store into 'result'
> ```
>
> Our bytecode supports about 30 opcodes including: `PUSH`, `POP`, `LOAD`, `STORE` for data movement; `ADD`, `SUB`, `MUL`, `DIV` for arithmetic; `EQ`, `LT`, `GT` for comparison; `JMP`, `JZ` for control flow; `CALL`, `RET` for function calls; and `PRINT`, `INPUT` for I/O.
>
> The code generator does a **two-pass translation**. The first pass generates bytecode and records label positions. The second pass **resolves all jump targets** — replacing label names with actual bytecode addresses. This is similar to how real assemblers work.
>
> Now let me hand over to [Speaker 5] who will explain the runtime environment and show you a live demo.

---
---

# SPEAKER 5: Virtual Machine, Demo & Conclusion (~6 min)

---

## SLIDE: Stage 7 — Virtual Machine (Runtime Environment)

> Thank you, [Speaker 4]. The final stage of our compiler is the **Virtual Machine** — this is our runtime environment. The VM takes the bytecode produced by the code generator and executes it instruction by instruction.
>
> Our VM is a **stack-based virtual machine**, similar in concept to the Java Virtual Machine or Python's bytecode interpreter. It has four main components:
>
> **The Operand Stack** — this is where all computation happens. When we compute `a + b`, we push `a`, push `b`, then execute `ADD` which pops both and pushes the result.
>
> **The Call Stack** — this maintains **stack frames** for function calls. Each frame stores the return address, local variables, and a saved stack pointer. When we call a function, we push a new frame. When we return, we pop the frame and jump back.
>
> **Memory** — this stores global variables and provides variable lookup.
>
> **The Heap** — this is where arrays are allocated. When you declare `var arr: int[10]`, the VM allocates an array of 10 elements on the heap.
>
> The VM also has an **instruction pointer** that tracks the current bytecode position, and it supports **execution tracing** — where it logs every instruction executed along with the stack state. This is extremely useful for debugging.

---

## SLIDE: VM Execution Example

> Let me trace through a simple example. Say we have the bytecode for `print(3 + 5)`:
>
> | Step | Instruction | Stack (after) |
> |------|------------|---------------|
> | 1 | `PUSH 3` | [3] |
> | 2 | `PUSH 5` | [3, 5] |
> | 3 | `ADD` | [8] |
> | 4 | `PRINT` | [] → outputs "8" |
>
> You can see how the stack grows and shrinks as values are pushed, consumed by operations, and printed. For function calls, the VM saves the current state in a stack frame, jumps to the function's bytecode, and when the function returns, restores the state and continues execution. This enables recursion — each recursive call gets its own stack frame with its own local variables.

---

## SLIDE: Live Demo

> Now, let me show you all of this in action. We built an **interactive web-based visualizer** that lets you step through every compiler stage.

**[SWITCH TO BROWSER — open http://localhost:8080]**

> This is our compiler visualizer. On the left, you can see the source code editor. I will load the Fibonacci example.

**[Select "Fibonacci" from the dropdown]**

> Here is the Fibonacci program — a recursive function that computes the Fibonacci sequence. Now let me click **Compile & Run**.

**[Click Compile & Run]**

> And immediately, we can see the output of every stage. Let me walk you through:
>
> **Stage 1 — Tokens**: You can see every token the lexer produced — keywords like `func`, `if`, `return` are highlighted in purple. Identifiers in blue. Literals in green. Operators and delimiters in orange. Each token has its line and column number.

**[Click AST tab]**

> **Stage 2 — AST**: Here is the Abstract Syntax Tree. You can see the hierarchical structure — the Program contains Functions, each Function has parameters and a body Block, and inside you can see If statements, Return statements, and BinaryOp expressions showing how the arithmetic is structured.

**[Click Semantic tab]**

> **Stage 3 — Semantic Analysis**: Here is the symbol table. It shows `fibonacci` as a function taking an `int` parameter and returning `int`, and `main` as a void function. All type checks passed.

**[Click IR (TAC) tab]**

> **Stage 4 — Three-Address Code**: Here you can see the linear intermediate representation. Notice the temporary variables `t0`, `t1`, the `IF_FALSE` conditional jumps, and the `CALL` instructions for the recursive calls.

**[Click Optimizer tab]**

> **Stage 5 — Optimization**: You can see the optimization report — how many constant folding operations, how many propagations, how many dead codes were eliminated. And below, the optimized TAC.

**[Click Bytecode tab]**

> **Stage 6 — Bytecode**: Here is the final bytecode — each instruction has an address, an opcode, and an operand. You can see `PUSH`, `LOAD`, `STORE`, `CALL`, `JZ` for conditional jumps, and so on. The function entry points are shown at the top.

**[Click Output tab]**

> And **Stage 7 — the Output**: The VM executed the bytecode and produced the Fibonacci sequence: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34. All correct! You can also see the execution trace showing every VM step.

---

## SLIDE: Summary

> To summarize what we have built:
>
> Our MiniLang compiler covers **all seven stages** of compiler design:
>
> 1. **Lexer** — hand-written character-by-character scanner
> 2. **Parser** — recursive descent, top-down, LL(1)
> 3. **Semantic Analyzer** — type checking, scoping, symbol tables
> 4. **IR Generator** — Three-Address Code
> 5. **Optimizer** — five optimization passes
> 6. **Code Generator** — stack-based bytecode
> 7. **Virtual Machine** — runtime environment with call stack and heap
>
> Everything was implemented from scratch in Python with **zero external dependencies**. No parser generators, no regex engines in the lexer — all hand-written to demonstrate understanding of the underlying theory.
>
> We also built the interactive web visualizer you just saw, which lets you step through every stage for any MiniLang program.
>
> Thank you. We are happy to take any questions.

---
---

# 📝 TIPS FOR THE PRESENTATION

1. **Practice transitions** — each speaker should introduce the next one by name
2. **Have the visualizer ready** — start `python server.py` before the presentation
3. **Keep the browser tab open** at http://localhost:8080
4. **If asked about bottom-up parsing**: "We implemented top-down recursive descent because it maps directly to grammar rules. Bottom-up parsers like LR/SLR are more powerful but typically generated by tools like Yacc — since we wanted to hand-write everything, recursive descent was the natural choice."
5. **If asked why Python**: "Python lets us focus on the compiler concepts without getting bogged down in memory management. The algorithms and data structures are the same regardless of implementation language."
6. **If asked about real assembly**: "We generate bytecode for a custom VM instead of x86 assembly. This still demonstrates all compiler stages, and the VM itself serves as our runtime environment. Real compilers like Java and Python also target VMs."

---

# 🔧 BEFORE THE PRESENTATION

Run these commands to make sure everything works:

```bash
cd "/Users/agaba/Desktop/School/Compiler/compiler presentation"

# Test the compiler
python3 main.py run examples/fibonacci.mini
python3 main.py run examples/factorial.mini

# Start the visualizer (keep this running)
python3 server.py
# Then open http://localhost:8080 in your browser
```
