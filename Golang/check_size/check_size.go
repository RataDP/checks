package main

/*

  ________   _______  ________  _________  _______   ________
  |\_____  \ /  ___  \|\   __  \|\___   ___\\  ___ \ |\   ____\
  \|___/  //__/|_/  /\ \  \|\  \|___ \  \_\ \   __/|\ \  \___|
      /  / /__|//  / /\ \  \\\  \   \ \  \ \ \  \_|/_\ \  \
     /  / /    /  /_/__\ \  \\\  \   \ \  \ \ \  \_|\ \ \  \____
    /__/ /    |\________\ \_______\   \ \__\ \ \_______\ \_______\
    |__|/      \|_______|\|_______|    \|__|  \|_______|\|_______|

    http://www.720tec.es
    Borja Blasco García <bblasco@720tec.es>
    Check size - Check the size of a file
    Version 1.2

 NOTE: Both flags, -w and -c must be set for alerts. For now, just with just one the check will fail.

 USAGE: checkSize -path <path_to_file> -file <file> [-w <size>[k|m|g]] [-c <size>[k|m|g]] [-name <service_name>]
 Default size by Bytes
*/
import (
	"bytes"
	"flag"
	"fmt"
	"os"
	"strconv"
	"strings"
)

type CheckStatus struct {
	code      int
	message   string
	checkName string
	file      string
	pathfile  string
	warn      int
	warnParam string
	crit      int
	critParam string
	value     int64
}

var status CheckStatus

func main() {

	path := flag.String("path", "", "Path to file")
	file := flag.String("file", "", "File's name")
	warn := flag.String("w", "", "When warning is triggered")
	crit := flag.String("c", "", "When critical is triggered")
	name := flag.String("name", "", "Name for the service")

	flag.Parse()

	if *path == "" || *file == "" {
		error(3, "USAGE: checkSize -path <path_to_file> -file <file> [-w <size>[k|m|g]] [-c <size>[k|m|g]] [-name <service_name>]")
		return
	}
	status.checkName = *name
	status.file = *file
	// Reemplazar . (dots) por -, genera un fallo con el check
	status.file = strings.Replace(status.file, ".", "-", -1)

	status.warnParam = *warn
	status.critParam = *crit
	if *warn != "" && *crit != "" {
		units := [2]string{*warn, *crit}
		// Tratar la unidad para transformarlo a bytes
		for i, ele := range units { // El primer elemento es el indice
			var letter byte = ele[len(ele)-1] // Conseguir la letra final
			var value int

			if letter >= '0' && letter <= '9' {
				// El ultimo caracter es un numero
				val, err := strconv.Atoi(ele)
				if err != nil {
					error(3, "Error casting -w or -c")
				}
				value = val
			} else {
				// El ultimo caracter puede ser una letra
				val, err := strconv.Atoi(ele[:len(ele)-1])
				if err != nil {
					error(3, "Error casting -w or -c")
				}
				switch letter {
				case 'K', 'k':
					value = val * (1 << 10)
				case 'M', 'm':
					value = val * (1 << 20)
				case 'G', 'g':
					value = val * (1 << 30)
				default:
					error(3, "Wrong unit on -w or -c. Avaliable K,M,G")
				}
			}
			// rellnar con el valor en bytes
			if i == 0 {
				status.warn = value
			} else {
				status.crit = value
			}
		}
	}
	if status.warn > status.crit {
		error(3, "Warning value is higher than Critical.")
	}

	var pa string = *path
	var addSlash bool
	if pa[len(pa)-1] != os.PathSeparator {
		addSlash = true
	}
	// Concatener path y fichero
	var buff bytes.Buffer
	buff.WriteString(*path)
	if addSlash {
		buff.WriteString(string(os.PathSeparator))
	}
	buff.WriteString(*file)
	status.pathfile = buff.String()
	check()

	fmt.Println(output())
	os.Exit(status.code)
}

// check is the main function. Performs the check
func check() {
	fileStat, err := os.Stat(status.pathfile)

	if err != nil {
		error(3, fmt.Sprintf("Error opening file %s", status.pathfile))
	}

	if fm := fileStat.Mode(); fm.IsDir() {
		error(3, "File is a directory")
	}

	status.value = fileStat.Size()

	switch {
	case status.critParam == "" && status.warnParam == "":
		status.code = 0
	case status.critParam != "" && status.value > int64(status.crit):
		status.code = 2
	case status.warnParam != "" && status.value > int64(status.warn):
		status.code = 1
	}
}

// output Print the result of the check
func output() string {
	var out string
	if status.code != 3 {
		switch status.code {
		case 0:
			status.message = " OK - "
		case 1:
			status.message = " WARN - "
		case 2:
			status.message = " CRIT - "
		}
		status.message += "File " + status.file + " " + size()

		if status.warnParam != "" && status.critParam != "" {
			status.message += " (" + status.warnParam + "/" + status.critParam + ")"
			// out = fmt.Sprintf("%d Size_%s size=%d;%d;%d %s", status.code, status.checkName, status.value, status.warn, status.crit, status.message)
			out = fmt.Sprintf("%s|size=%d;%d;%d;;", status.message, status.value, status.warn, status.crit)
		} else {
			// out = fmt.Sprintf("%d Size_%s size=%d %s", status.code, status.checkName, status.value, status.message)
			out = fmt.Sprintf("%s|size=%d;;;;", status.message, status.value)
		}
		return out
	}
	status.message = "UNK - " + status.message
	// out = fmt.Sprintf("%d Size_%s - %s", status.code, status.checkName, status.message)
	out = fmt.Sprintf("%s", status.message)
	return out
}

func error(code int, message string) {
	status.code = code
	status.message = message
	fmt.Println(output())
	os.Exit(code)
}

// Summarize the size of the file
// output: string size with unit
func size() string {
	var m float64 = 1
	var v float64 = float64(status.value)
	var i int = 0
	for v/m > 1024 {
		m = m * 1024
		i++
	}
	switch i {
	case 0:
		return fmt.Sprintf("%.2f B", v/m)
	case 1:
		return fmt.Sprintf("%.2f KB", v/m)
	case 2:
		return fmt.Sprintf("%.2f MB", v/m)
	case 3:
		return fmt.Sprintf("%.2f GB", v/m)
	}
	return "Not ready for this size, larger than TB"
}
