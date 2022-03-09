# pkgbuilder
pkgbuilder is a simple JSON-file based wrapper script that builds a gcc
toolchain (e.g., for ARM Cortex-M) painlessly.

## Usage
You need a recipe file, which you simply can run:

```
$ cat arm_cm3.json
{
	"name": "cm3",
	"target": "~/bin/gcc/arm-cm3/",
	"arch": "arm-cortex-m3",
	"ingredients": [
		{ "name": "binutils" },
		{ "name": "gcc", "flags": [ "bootstrap" ] },
		{ "name": "newlib" },
		{ "name": "gcc", "flags": [ "lang-c" ] },
		{ "name": "gdb" }
	]
}
$ ./pktbuilder arm_cm3.json 
```

## License
GNU GPL-3.
