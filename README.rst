Pysh
====
Every day we stray further from God's light.

What is this?
-------------
Pysh is a shell-script like language. Like shell scripts it is good for controling the flow of the execution of
programs.

This repo contains the implementation of pysh in python.


Why would you do this?
----------------------
The aim of pysh is to create an implementation of the posix shell that can run on many platforms. This way, shell
scripts written against pysh do not need to wory about running on differing shells. These shell scripts will have the
same behaviour on every single platform.

With pysh it should also be able to sandbox the commands that can be ran, and common useful commands can be replaced
with pysh-provided replacements that will have consistent behaviour across platforms.

Also, compilers are just fun to write :)

How does it work?
-----------------
Pysh consists of a lexer, a parser, and a pysh bytecode generator. Pysh bytecode can be ran by a pysh interpreter. This
repo is an implementation of all of those components. Maybe later someone could hook pysh up to llvm to create jit/aot
shell scripts? Wait, stop! don't actually do that! Forget I even said that.

Is it done?
-----------
No

Is it stable? Can I use this in production?
-------------------------------------------
Go away
