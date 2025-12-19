# Java Query Runner for Catholic Semantic Canon

This example demonstrates how to query the Catholic Semantic Canon ontology using **Apache Jena** in Java.

## Prerequisites

- **Java 17+** (or Java 11+ with pom.xml adjustments)
- **Maven 3.6+**

### Installing Java

**Ubuntu/Debian:**
```bash
sudo apt install openjdk-17-jdk
```

**macOS (Homebrew):**
```bash
brew install openjdk@17
```

**Windows:** Download from https://adoptium.net/ or use `winget install EclipseAdoptium.Temurin.17.JDK`

### Installing Maven

**Ubuntu/Debian:**
```bash
sudo apt install maven
```

**macOS (Homebrew):**
```bash
brew install maven
```

**Windows:** Download from https://maven.apache.org/download.cgi and follow the [installation guide](https://maven.apache.org/install.html), or use `winget install Apache.Maven`

Verify installation:
```bash
java -version
mvn -version
```

---

## Quick Start

```bash
cd examples/java

# Run with Maven (interactive menu)
mvn compile exec:java

# Run a specific query
mvn compile exec:java -Dexec.args="01"

# List all available queries
mvn compile exec:java -Dexec.args="--list"
```

## Building an Executable JAR

```bash
mvn package
java -jar target/semantic-canon-query-runner-1.0.0.jar
java -jar target/semantic-canon-query-runner-1.0.0.jar 01
java -jar target/semantic-canon-query-runner-1.0.0.jar --list
```

## Why Java/Apache Jena?

Apache Jena is a mature, stable RDF/SPARQL library that handles the Catholic Semantic Canon ontology (120,000+ triples) reliably. Unlike some other RDF libraries, Jena:

- Parses both Turtle (.ttl) and OWL/XML (.owl) formats without issues
- Handles complex SPARQL queries consistently
- Provides excellent performance for large ontologies

---

## Installing Apache Jena Globally

If you want to use Apache Jena's command-line tools (like `arq`) outside of Maven, you can install Jena globally.

### Linux / macOS / WSL

```bash
# Create a tools directory (or use your preferred location)
mkdir -p ~/tools
cd ~/tools

# Download Apache Jena (check https://jena.apache.org/download/ for latest version)
wget https://dlcdn.apache.org/jena/binaries/apache-jena-5.6.0.tar.gz

# Extract and clean up
tar -xzf apache-jena-5.6.0.tar.gz
rm apache-jena-5.6.0.tar.gz

# Add to PATH (for bash)
echo 'export JENA_HOME="$HOME/tools/apache-jena-5.6.0"' >> ~/.bashrc
echo 'export PATH="$PATH:$JENA_HOME/bin"' >> ~/.bashrc
source ~/.bashrc

# For zsh users, use ~/.zshrc instead:
# echo 'export JENA_HOME="$HOME/tools/apache-jena-5.6.0"' >> ~/.zshrc
# echo 'export PATH="$PATH:$JENA_HOME/bin"' >> ~/.zshrc
# source ~/.zshrc
```

### Windows (PowerShell)

1. Download from https://jena.apache.org/download/
2. Extract to a folder like `C:\tools\apache-jena-5.6.0`
3. Add to PATH via System Properties > Environment Variables:
   - Add `JENA_HOME` = `C:\tools\apache-jena-5.6.0`
   - Add `%JENA_HOME%\bat` to your PATH

### Verify Installation

```bash
arq --version
```

You should see output like:
```
Apache Jena ARQ - 5.6.0
```

---

## Using the `arq` Command-Line Tool

Once Jena is installed, you can run SPARQL queries directly from the command line:

```bash
# Navigate to the project root
cd /path/to/ontology-semantic-canon

# Run a query against the OWL file
arq --data=sources/ontology-semantic-canon.owl --query=queries/01-list-all-classes.rq

# Run against the Turtle file
arq --data=sources/ontology-semantic-canon.ttl --query=queries/03-find-church-hierarchy-roles.rq

# Run with output formatting
arq --data=sources/ontology-semantic-canon.owl --query=queries/01-list-all-classes.rq --results=CSV
arq --data=sources/ontology-semantic-canon.owl --query=queries/01-list-all-classes.rq --results=JSON
```

### Common `arq` Options

| Option | Description |
|--------|-------------|
| `--data=FILE` | Load RDF data from file |
| `--query=FILE` | Execute SPARQL query from file |
| `--results=FORMAT` | Output format: `text` (default), `CSV`, `TSV`, `JSON`, `XML` |
| `--quiet` | Suppress progress messages |
| `--time` | Show execution time |

---

## Other Jena Command-Line Tools

Apache Jena includes several other useful tools:

| Tool | Description |
|------|-------------|
| `arq` | Run SPARQL queries |
| `riot` | Parse/validate/convert RDF data |
| `tdb2.tdbloader` | Load data into TDB2 database |
| `fuseki-server` | Start a SPARQL endpoint server |

### Examples

```bash
# Validate/parse an RDF file
riot --validate sources/ontology-semantic-canon.ttl

# Convert Turtle to N-Triples
riot --output=ntriples sources/ontology-semantic-canon.ttl > output.nt

# Convert OWL to Turtle
riot --output=turtle sources/ontology-semantic-canon.owl > output.ttl
```

---

## Troubleshooting

### Maven not found

Install Maven:
- **Ubuntu/Debian**: `sudo apt install maven`
- **macOS**: `brew install maven`
- **Windows**: Download from https://maven.apache.org/download.cgi

### Java version errors

Ensure you have Java 17+:
```bash
java -version
```

If you need Java 11 compatibility, update `pom.xml`:
```xml
<maven.compiler.source>11</maven.compiler.source>
<maven.compiler.target>11</maven.compiler.target>
```

### Logging warnings

SLF4J warnings are normal and don't affect functionality. To silence them, the project includes `slf4j-simple` as a dependency.
