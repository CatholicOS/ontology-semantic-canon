package org.catholicos;

import org.apache.jena.query.*;
import org.apache.jena.rdf.model.Model;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.riot.RDFDataMgr;
import org.apache.jena.riot.RDFFormat;

import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.stream.Collectors;

/**
 * Catholic Semantic Canon - SPARQL Query Runner
 *
 * This application loads the ontology and runs SPARQL queries from the queries/ folder.
 *
 * Usage:
 *     mvn exec:java                                    # Interactive menu
 *     mvn exec:java -Dexec.args="01"                   # Run query 01-list-all-classes.rq
 *     mvn exec:java -Dexec.args="--list"              # List available queries
 *     mvn exec:java -Dexec.args="--query 'SELECT...'" # Run inline SPARQL
 */
public class QueryRunner {

    private static final Path PROJECT_ROOT = findProjectRoot();
    private static final Path SOURCES_DIR = PROJECT_ROOT.resolve("sources");
    private static final Path QUERIES_DIR = PROJECT_ROOT.resolve("queries");
    private static final Path DEFAULT_ONTOLOGY = SOURCES_DIR.resolve("ontology-semantic-canon.ttl");

    private Model model;

    public static void main(String[] args) {
        QueryRunner runner = new QueryRunner();
        runner.run(args);
    }

    private static Path findProjectRoot() {
        // Start from current directory and look for sources/ folder
        Path current = Paths.get("").toAbsolutePath();

        // If we're in examples/java, go up two levels
        if (current.endsWith("java") || current.toString().contains("examples")) {
            current = current.getParent();
            if (current != null && current.endsWith("examples")) {
                current = current.getParent();
            }
        }

        // Check if sources exists here
        if (Files.exists(current.resolve("sources"))) {
            return current;
        }

        // Try going up from current directory
        while (current != null) {
            if (Files.exists(current.resolve("sources"))) {
                return current;
            }
            current = current.getParent();
        }

        // Fallback to current directory
        return Paths.get("").toAbsolutePath();
    }

    public void run(String[] args) {
        List<String> argList = Arrays.asList(args);

        // Handle --list flag
        if (argList.contains("--list") || argList.contains("-l")) {
            listQueries();
            return;
        }

        // Handle --query flag
        int queryIdx = argList.indexOf("--query");
        if (queryIdx == -1) queryIdx = argList.indexOf("-q");
        if (queryIdx != -1 && queryIdx + 1 < argList.size()) {
            loadOntology(DEFAULT_ONTOLOGY);
            runInlineQuery(argList.get(queryIdx + 1));
            return;
        }

        // Load ontology for all other operations
        loadOntology(DEFAULT_ONTOLOGY);

        // Run specific query by number
        if (!argList.isEmpty() && !argList.get(0).startsWith("-")) {
            String queryNumber = argList.get(0);
            runQueryByNumber(queryNumber);
            return;
        }

        // Interactive mode
        interactiveMenu();
    }

    private void loadOntology(Path ontologyPath) {
        System.out.println("Loading ontology from " + ontologyPath.getFileName() + "...");

        model = ModelFactory.createDefaultModel();

        try {
            RDFDataMgr.read(model, ontologyPath.toString());
            System.out.println("Loaded " + model.size() + " triples.");
        } catch (Exception e) {
            System.err.println("Error loading ontology: " + e.getMessage());
            System.err.println("Expected path: " + ontologyPath);
            System.err.println("Make sure you're running from the project directory.");
            System.exit(1);
        }
    }

    private List<Path> getQueryFiles() {
        if (!Files.exists(QUERIES_DIR)) {
            System.err.println("Queries directory not found: " + QUERIES_DIR);
            return Collections.emptyList();
        }

        try {
            return Files.list(QUERIES_DIR)
                    .filter(p -> p.toString().endsWith(".rq"))
                    .sorted()
                    .collect(Collectors.toList());
        } catch (IOException e) {
            System.err.println("Error listing queries: " + e.getMessage());
            return Collections.emptyList();
        }
    }

    private void listQueries() {
        System.out.println("\nAvailable queries:");
        for (Path query : getQueryFiles()) {
            System.out.println("  " + query.getFileName());
        }
    }

    private void runQueryByNumber(String number) {
        List<Path> queries = getQueryFiles();
        Optional<Path> matching = queries.stream()
                .filter(q -> q.getFileName().toString().startsWith(number))
                .findFirst();

        if (matching.isPresent()) {
            runQueryFile(matching.get());
        } else {
            System.err.println("No query found matching '" + number + "'");
            System.err.println("Use --list to see available queries");
        }
    }

    private void runQueryFile(Path queryPath) {
        System.out.println("\n=== Running: " + queryPath.getFileName() + " ===\n");

        try {
            String queryText = Files.readString(queryPath);
            executeQuery(queryText);
        } catch (IOException e) {
            System.err.println("Error reading query file: " + e.getMessage());
        }
    }

    private void runInlineQuery(String queryText) {
        System.out.println("\n=== Running inline query ===\n");
        executeQuery(queryText);
    }

    private void executeQuery(String queryText) {
        try {
            Query query = QueryFactory.create(queryText);

            if (query.isConstructType()) {
                // CONSTRUCT query
                try (QueryExecution qe = QueryExecutionFactory.create(query, model)) {
                    Model resultModel = qe.execConstruct();
                    System.out.println("--- CONSTRUCT Results (Turtle format) ---\n");
                    RDFDataMgr.write(System.out, resultModel, RDFFormat.TURTLE_PRETTY);
                }
            } else if (query.isSelectType()) {
                // SELECT query
                try (QueryExecution qe = QueryExecutionFactory.create(query, model)) {
                    ResultSet results = qe.execSelect();

                    // Print header
                    List<String> vars = results.getResultVars();
                    System.out.println(String.join(" | ", vars));
                    System.out.println("-".repeat(vars.size() * 20));

                    int count = 0;
                    while (results.hasNext()) {
                        QuerySolution sol = results.next();
                        List<String> values = new ArrayList<>();
                        for (String var : vars) {
                            if (sol.get(var) != null) {
                                String val = sol.get(var).toString();
                                // Shorten URIs for readability
                                if (val.startsWith("http")) {
                                    int lastSlash = val.lastIndexOf('/');
                                    int lastHash = val.lastIndexOf('#');
                                    int idx = Math.max(lastSlash, lastHash);
                                    if (idx > 0) val = val.substring(idx + 1);
                                }
                                values.add(val);
                            } else {
                                values.add("");
                            }
                        }
                        System.out.println(String.join(" | ", values));
                        count++;
                    }
                    System.out.println("\n(" + count + " results)");
                }
            } else if (query.isAskType()) {
                // ASK query
                try (QueryExecution qe = QueryExecutionFactory.create(query, model)) {
                    boolean result = qe.execAsk();
                    System.out.println("Result: " + result);
                }
            }
        } catch (Exception e) {
            System.err.println("Query error: " + e.getMessage());
        }
    }

    private void interactiveMenu() {
        List<Path> queries = getQueryFiles();
        if (queries.isEmpty()) return;

        Scanner scanner = new Scanner(System.in);

        while (true) {
            System.out.println("\n" + "=".repeat(50));
            System.out.println("Available SPARQL Queries:");
            System.out.println("=".repeat(50));

            for (int i = 0; i < queries.size(); i++) {
                String name = queries.get(i).getFileName().toString();
                name = name.substring(0, name.length() - 3); // Remove .rq
                System.out.printf("  %2d. %s%n", i + 1, name);
            }

            System.out.println("\n  q. Quit");
            System.out.println("  c. Custom SPARQL query");
            System.out.println("=".repeat(50));

            System.out.print("\nSelect a query number (or 'q' to quit): ");
            String choice = scanner.nextLine().trim().toLowerCase();

            if (choice.equals("q")) {
                System.out.println("Goodbye!");
                break;
            } else if (choice.equals("c")) {
                System.out.println("\nEnter your SPARQL query (end with an empty line):");
                StringBuilder queryBuilder = new StringBuilder();
                String line;
                while (!(line = scanner.nextLine()).isEmpty()) {
                    queryBuilder.append(line).append("\n");
                }
                if (queryBuilder.length() > 0) {
                    executeQuery(queryBuilder.toString());
                }
            } else {
                try {
                    int idx = Integer.parseInt(choice) - 1;
                    if (idx >= 0 && idx < queries.size()) {
                        runQueryFile(queries.get(idx));
                    } else {
                        System.out.println("Invalid selection.");
                    }
                } catch (NumberFormatException e) {
                    System.out.println("Please enter a number.");
                }
            }
        }
    }
}
