# Conversation Export

## User

Explain the syntax for bash scripts. If statements, recieving number args, and executing commands.

---

## Assistant

Yep — for your Task 2 `safe_marker.sh`, the Bash pieces you care about are pretty small. The assignment specifically wants the script to accept exactly one argument, verify that it is `course-marker`, reject everything else, and then create only `hw1/markers/marker.txt`.

### Basic Bash script structure

A Bash script usually starts with a **shebang**:

```bash
#!/usr/bin/env bash
```

That tells Linux to run the file using Bash.

Then you write commands exactly like you would type them into the terminal:

```bash
echo "Hello"
pwd
touch file.txt
```

To make the script executable:

```bash
chmod +x script.sh
```

Then run it:

```bash
./script.sh
```

### Receiving command-line arguments

Suppose you run:

```bash
./script.sh apple banana 42
```

Bash gives you special variables:

```bash
$0    # script name: ./script.sh
$1    # apple
$2    # banana
$3    # 42

$#    # number of arguments: 3
"$@"  # all arguments, individually preserved
```

For your assignment, the really important ones are:

```bash
$#
$1
```

So:

```bash
if [[ $# -ne 1 ]]; then
    echo "Expected exactly one argument"
    exit 1
fi
```

means:

> If the number of arguments is not equal to 1, print an error and terminate.

### `if` statement syntax

The general form is:

```bash
if [[ condition ]]; then
    commands
elif [[ another_condition ]]; then
    commands
else
    commands
fi
```

Notice that Bash closes the `if` with:

```bash
fi
```

Basically `if` backwards. Very Unix-y.

For string comparisons:

```bash
if [[ "$1" == "course-marker" ]]; then
    echo "Correct argument"
fi
```

For "not equal":

```bash
if [[ "$1" != "course-marker" ]]; then
    echo "Invalid argument"
fi
```

For numeric comparisons, Bash commonly uses:

```bash
-eq    # equal
-ne    # not equal
-lt    # less than
-le    # less than or equal
-gt    # greater than
-ge    # greater than or equal
```

Example:

```bash
if [[ $# -gt 2 ]]; then
    echo "Too many arguments"
fi
```

So don't write:

```bash
[[ $# != 1 ]]
```

for numeric logic. Prefer:

```bash
[[ $# -ne 1 ]]
```

### Combining conditions

You can use `&&` for AND:

```bash
if [[ $# -eq 1 && "$1" == "course-marker" ]]; then
    echo "Valid"
fi
```

And `||` for OR:

```bash
if [[ $# -ne 1 || "$1" != "course-marker" ]]; then
    echo "Invalid"
fi
```

That second one is particularly relevant to your script:

```text
wrong number of arguments
OR
wrong argument
→ reject
```

### Executing commands

Inside a Bash script, you don't need anything special to execute a command.

This:

```bash
touch marker.txt
```

literally runs:

```bash
touch marker.txt
```

Same with:

```bash
echo "marker" > marker.txt
```

The `>` operator redirects the output of `echo` into the file.

So:

```bash
echo "hello"
```

prints to the terminal, while:

```bash
echo "hello" > file.txt
```

writes:

```text
hello
```

into `file.txt`.

`>` overwrites the file. `>>` appends:

```bash
echo "another line" >> file.txt
```

### Variables

Create a variable without `$`:

```bash
name="Jacob"
```

Read it using `$`:

```bash
echo "$name"
```

Generally, quote variables:

```bash
echo "$name"
touch "$filename"
```

rather than:

```bash
echo $name
touch $filename
```

Quoting prevents spaces and certain special characters from being interpreted unexpectedly.

For example:

```bash
file="my file.txt"

touch "$file"
```

creates one file:

```text
my file.txt
```

Without quotes:

```bash
touch $file
```

Bash would interpret it as:

```bash
touch my file.txt
```

and create two files.

### Exiting the script

Use:

```bash
exit 0
```

for success and:

```bash
exit 1
```

for failure.

Linux commands return an **exit status**:

```text
0 = success
nonzero = failure
```

You can inspect the most recent command's status with:

```bash
echo $?
```

For example:

```bash
touch test.txt
echo $?
```

probably prints:

```text
0
```

### Commands chained together

Bash also lets you conditionally execute commands.

```bash
command1 && command2
```

means:

> Run `command2` only if `command1` succeeded.

For example:

```bash
mkdir test && cd test
```

`cd test` only happens if `mkdir test` worked.

Conversely:

```bash
command1 || command2
```

means:

> Run `command2` only if `command1` failed.

Example:

```bash
cd some_directory || exit 1
```

### Putting the pieces together

A simplified example using the same concepts your Task 2 needs would be:

```bash
#!/usr/bin/env bash

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <argument>"
    exit 1
fi

if [[ "$1" != "expected-value" ]]; then
    echo "Invalid argument"
    exit 1
fi

echo "Argument accepted"

touch example.txt

exit 0
```

If you run:

```bash
./script.sh
```

it fails because `$#` is `0`.

If you run:

```bash
./script.sh hello world
```

it fails because `$#` is `2`.

If you run:

```bash
./script.sh wrong
```

then `$#` is `1`, but `$1` is wrong.

And:

```bash
./script.sh expected-value
```

passes both checks and runs `touch`.

For your specific homework, mentally translate that final example into:

```text
$# must equal 1

AND

$1 must equal "course-marker"

THEN

create the fixed marker file
```

The key security idea is that **the argument should only be checked, not executed**. Something dangerous-looking like:

```bash
$1
```

would tell Bash to treat the user's argument as a command. Your assignment explicitly says the script must "never run another program supplied by user input," so `$1` should be data you compare, not a command you execute.

---

## User

Export and format our entire conversation so far as a clean Markdown (.md) code block or downloadable file.