# Minecraft-Script Data Types

Minecraft-Script values are dynamically typed. A variable can hold any value, and
the value's behavior is determined by the operation or function that uses it.

When a script is compiled to a datapack, values are stored in Minecraft storage
and scoreboard data. This means some operations follow Minecraft command
semantics: numbers are integers, booleans compile to numeric truth values, and
some text component fields must be known at compile time.

## Strings

Strings store text. They are commonly used for chat output, Minecraft command
fragments, block ids, item ids, selector targets, coordinates, and text component
properties.

### Literals
Strings can be written with double quotes, single quotes, or backticks.

```js
var greeting = "Hello";
var block = 'minecraft:diamond_block';
var command_text = `say Hello from Minecraft-Script`;
```

String literals do not currently support escape sequences. Use a different quote
style if the text needs to contain a quote character.

```js
var message = "It's working!";
```

### Indexing
Strings can be indexed with square brackets. Indexes start at 0.

```js
var name = "Steve";
log(name[0]);  // logs "S"
```

### Concatenation
Use the builtin `concatenate()` function when building dynamic strings for
compiled datapacks.

```js
var target = "@a";
var cmd = concatenate("say Hello ", target);
command(cmd);
```

The `+` operator is primarily numeric in compiled datapacks. Prefer
`concatenate()` for text.

## Numbers

Numbers are integers. They are used for arithmetic, counts, loop ranges,
indexes, custom model data, and command parameters.

### Literals
Number literals are written as digits.

```js
var count = 5;
var height = 64;
```

Negative values are created with unary `-`.

```js
var offset = -1;
```

Decimals are not supported as number literals.

### Arithmetic
Numbers support the standard arithmetic operators.

```js
var value = 10;

log(value + 2);  // 12
log(value - 2);  // 8
log(value * 2);  // 20
log(value / 3);  // 3
log(value % 3);  // 1
```

Division is integer division.

### Comparisons
Comparisons return booleans.

```js
var score = 10;

log(score == 10);
log(score > 5);
log(score <= 20);
```

## Booleans

Booleans represent true or false values. The literals are `true` and `false`.

```js
var is_enabled = true;
var has_started = false;
```

Booleans are most often used in `if`, `while`, and `async while` conditions.

```js
var is_open = true;

if (is_open) {
    log("open");
}
```

### Boolean operations
Use `!` to invert a boolean value.

```js
var is_hidden = false;
log(!is_hidden);  // true
```

Boolean connectors are available with `&&` and `||`.

```js
var has_key = true;
var door_locked = false;

if (has_key && !door_locked) {
    log("You can enter");
}
```

When compiled, boolean values are represented with Minecraft-friendly numeric
truth values. In chat output, true values may appear as `1` and false values as
`0` depending on the context.

## Null

`null` represents the absence of a useful value. Variables declared without a
value are initialized to `null`, and functions that do not return another value
produce `null`.

```js
var pending;
log(pending);  // null
```

Use `null` when a variable needs to exist before a later assignment.

```js
var selected_block;
set selected_block = get_block("~", "~-1", "~");
```

## Lists

Lists store ordered values. A list can contain mixed value types.

```js
var values = [1, "two", true, null];
```

Lists can also be empty.

```js
var saved_blocks = [];
```

### Indexing
Indexes start at 0.

```js
var blocks = ["minecraft:dirt", "minecraft:stone", "minecraft:glass"];
log(blocks[1]);  // minecraft:stone
```

Use `set` with an index to replace a value.

```js
var blocks = ["minecraft:dirt", "minecraft:stone"];
set blocks[0] = "minecraft:grass_block";
```

### Appending
Use the builtin `append()` function to add an item to the end of a list in
compiled datapacks.

```js
var blocks = [];
append(blocks, "minecraft:dirt");
append(blocks, "minecraft:stone");
```

### Iteration
Lists can be used in `for` loops.

```js
var blocks = ["minecraft:dirt", "minecraft:stone", "minecraft:glass"];

for (block in blocks) {
    set_block("~", "~-1", "~", block);
}
```

Use `range()` when looping over numeric indexes.

```js
var blocks = ["minecraft:dirt", "minecraft:stone", "minecraft:glass"];

for (i in range(3)) {
    log(blocks[i]);
}
```

## Functions

Functions are values that contain reusable script logic. They can be called by
name, passed to builtins, and used for callback-style behavior such as clickable
items and raycasts.

```js
function greet(name) {
    log("Hello", name);
}

greet("Steve");
```

Functions that do not explicitly return another value return `null`.

### Callback functions
Some builtins expect function values.

```js
function on_click() {
    command("say clicked");
}

@a give_clickable_item(on_click, "Click Me");
```

```js
function on_hit() {
    set_block("~", "~", "~", "minecraft:diamond_block");
}

function trail() {
    command("particle minecraft:end_rod ~ ~ ~ 0 0 0 0 1 force");
}

@a raycast_block(on_hit, 10, trail);
```

### Scoreboard event functions
Functions can subscribe to scoreboard criteria with `on`.

```js
function reward() on "minecraft.mined:minecraft.diamond_ore" {
    give_item("minecraft:diamond", "", 1);
}
```

Scoreboard event functions run as each player whose tracked score is greater
than zero, then reset that player's score. They cannot take parameters.

## Text Components

Text components represent Minecraft rich text for chat, titles, hover text, and
click events. Create them with `text()` and chain builder methods.

```js
var message = text().text("Hello ").color("gold").bold().append(
    text().text("World!").color("yellow")
);

tellraw("@a", message);
```

Common builder methods include:

| Method | Description |
|--------|-------------|
| `.text("...")` | Set plain text content |
| `.color("gold")` | Set a named or hex color |
| `.bold()`, `.italic()`, `.underlined()` | Apply formatting |
| `.strikethrough()`, `.obfuscated()` | Apply extra formatting |
| `.font("...")` | Set the font id |
| `.insertion("...")` | Set shift-click insertion text |
| `.translate("key")` | Use a Minecraft translation key |
| `.append(other)` | Append another text component |
| `.click_run("...")` | Run a command when clicked |
| `.click_suggest("...")` | Suggest a command in chat |
| `.click_open_url("...")` | Open a URL |
| `.click_copy("...")` | Copy text to the clipboard |
| `.hover_text("...")` | Show hover text |
| `.hover_item("minecraft:diamond")` | Show an item tooltip |

Use `tellraw()`, `title()`, and `title_times()` to display text components.

```js
title_times("@a", 10, 60, 20);
title("@a", "title", text().text("Welcome").color("green").bold());
title("@a", "subtitle", text().text("Built with Minecraft-Script"));
```

Some text component properties, such as colors, click actions, translation keys,
and hover item ids, must be string literals at compile time.

## Unknown Values

Some compiled operations produce values whose exact type is only known by
Minecraft at runtime. For example, indexing a list or reading a block from the
world may produce a value that the compiler stores and passes through without
fully knowing its type.

```js
var blocks = ["minecraft:dirt", "minecraft:stone"];
var selected = blocks[0];

log(selected);
```

Unknown values can usually be logged, assigned, passed to functions, or copied
into Minecraft commands through builtins. If an operation requires a specific
compile-time type, the compiler may reject an unknown value.

## Type Conversion Notes

Minecraft-Script does not currently have general-purpose type conversion
functions. Use the value in the form expected by the builtin or command you are
calling.

Common patterns:

- Use strings for Minecraft ids, selectors, coordinates, and command fragments.
- Use numbers for counts, indexes, ranges, and arithmetic.
- Use booleans for conditions.
- Use `concatenate()` to build dynamic command strings.
- Use text components for rich chat/title output instead of hand-written JSON.
