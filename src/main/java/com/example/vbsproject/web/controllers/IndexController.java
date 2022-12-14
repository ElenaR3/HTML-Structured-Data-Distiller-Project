package com.example.vbsproject.web.controllers;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;

import com.example.vbsproject.service.FileExport;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.jena.rdf.model.ModelFactory;
import org.apache.jena.riot.RDFLanguages;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.configurationprocessor.json.JSONException;
import org.springframework.boot.configurationprocessor.json.JSONObject;
import org.springframework.http.*;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
@RequestMapping({ "/", "/index" })
public class IndexController {

    @Autowired
    private FileExport fileExporter;

    public static String UPLOAD_DIRECTORY = "src\\main\\resources\\uploads";

    @GetMapping
    public String main(Model model) {

        List<String> formats = Arrays.asList("RDFa", "Microdata", "Turtle in HTML", "JSON-LD");
        model.addAttribute("formats", formats);

        return "index";
    }

    @GetMapping("{tab}")
    public String tab(@PathVariable String tab, Model model) {

        if(!tab.equals("tab4")) {
            List<String> formats = Arrays.asList("RDFa", "Microdata", "Turtle in HTML", "JSON-LD");
            model.addAttribute("formats", formats);
        } else {
            List<String> formats = Arrays.asList("RDFa", "Microdata","JSON-LD");
            model.addAttribute("formats", formats);
        }

        List<String> outputFormats = Arrays.asList("RDF/XML", "N-triples", "Turtle", "JSON-LD");
        model.addAttribute("outputFormats", outputFormats);
        model.addAttribute("check", false);

        if (Arrays.asList("tab1", "tab2", "tab3", "tab4")
                .contains(tab)) {
            return "_" + tab;
        }
        return "empty";
    }

    @PostMapping("/postUrl")
    public String create(@RequestParam String uri, @RequestParam String [] formats, String outputFormat, Model model) throws IOException, JSONException, ClassNotFoundException {
        model.addAttribute("uri", uri);
        return this.getDataFromUrl(uri, formats, outputFormat, model);

    }

    @PostMapping("/postFile")
    public String uploadFile(Model model, @RequestParam MultipartFile myfile, @RequestParam String [] formats,
                             RedirectAttributes attributes) throws IOException, JSONException {
        StringBuilder fileNames = new StringBuilder();
        Path fileNameAndPath = Paths.get(UPLOAD_DIRECTORY, myfile.getOriginalFilename());
        fileNames.append(myfile.getOriginalFilename());
        Files.write(fileNameAndPath, myfile.getBytes());
        model.addAttribute("msg", "Uploaded images: " + fileNames.toString());

        StringBuilder sb = new StringBuilder();

        try (BufferedReader br = Files.newBufferedReader(fileNameAndPath)) {

            // read line by line
            String line;
            while ((line = br.readLine()) != null) {
                sb.append(line).append("\n");
            }

        } catch (IOException e) {
            System.err.format("IOException: %s%n", e);
        }

        String data = sb.toString();

        return this.getDataFromHtml(data,formats, model);

    }

    @PostMapping("/postText")
    public String exploreText(@RequestParam String textArea, @RequestParam String [] formats,
                              Model model) throws IOException, InterruptedException, JSONException, ClassNotFoundException {

        return this.getDataFromHtml(textArea,formats, model);
    }

    @GetMapping("/getData")

    public String getDataFromUrl(@RequestBody String url, @RequestParam String [] formats,
                          @RequestParam String outputFormat, Model model1) throws IOException, JSONException {

        String externalApi = "http://127.0.0.1:2000/result";
        String externalApiTurtle = "http://127.0.0.1:2000/turtle";
        String externalApiRdfa = "http://127.0.0.1:2000/rdfa";
        String externalApiMicrodata = "http://127.0.0.1:2000/microdata";

        RestTemplate restTemplate = new RestTemplate();
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        JSONObject JsonObject = new JSONObject();
        JsonObject.put("url", url);
        JsonObject.put("outputFormat", outputFormat.toLowerCase());


        final ObjectMapper objectMapper = new ObjectMapper();
        HttpEntity<String> request =
                new HttpEntity<String>(JsonObject.toString(), headers);

        String resultAsJsonStr = restTemplate.postForObject(externalApi, request, String.class);
        JsonNode root = objectMapper.readTree(resultAsJsonStr);
        JsonNode nodeRDFA = root.get("rdfa");
        JsonNode nodeMicrodata = root.get("microdata");


        String result_turtle = restTemplate.postForObject(externalApiTurtle, request, String.class);
        String result_rdfa = "RDFa data was not found";
        String result_microdata = "Microdata data was not found";

        if(nodeRDFA.size() != 0) {
            result_rdfa = restTemplate.postForObject(externalApiRdfa, request, String.class);

            if(Objects.equals(result_rdfa, "")) {
                result_rdfa = "RDFa data was not found.";
            }
        }

        if(nodeMicrodata.size() != 0) {
            result_microdata = restTemplate.postForObject(externalApiMicrodata, request, String.class);

            if(outputFormat.equals("RDF/XML")) {
                String name = nodeMicrodata.toString();
                InputStream targetStream = new ByteArrayInputStream(name.substring(1, name.length()-1).getBytes());
                org.apache.jena.rdf.model.Model model = ModelFactory.createDefaultModel();
                model.read(targetStream, null, "JSON-LD");
                ByteArrayOutputStream out = new ByteArrayOutputStream();
                model.write(out, RDFLanguages.RDFXML.getLabel());
                result_microdata = out.toString(StandardCharsets.UTF_8);

            }
            if(Objects.equals(result_microdata, "")) {
                result_microdata = "Microdata was not found.";
            }
        }

        String result_json_ld = null;

        if(result_turtle == null && (Arrays.asList(formats).contains("Turtle in HTML"))) {
            result_turtle = "Turtle embedded in HTML was not found.";
        }

        if(!(Arrays.asList(formats).contains("Turtle in HTML"))) {
            result_turtle = "No search for Turtle in HTML was done.";
        }

        if(!Arrays.asList(formats).contains("RDFa")) {
            result_rdfa = "No search for RDFa was done.";
        }

        if(!Arrays.asList(formats).contains("Microdata")) {
            result_microdata = "No search for Microdata was done.";
        }


            if (Arrays.asList(formats).contains("JSON-LD")) {
                JsonNode nameNode = root.get("json-ld");
                String name;
                if (nameNode.size() != 0) {
                    name = nameNode.toString();
                    InputStream targetStream = new ByteArrayInputStream(name.substring(1, name.length()-1).getBytes());
                    org.apache.jena.rdf.model.Model model = ModelFactory.createDefaultModel();
                    model.read(targetStream, null, "JSON-LD");

                    ByteArrayOutputStream out = new ByteArrayOutputStream();
                    switch (outputFormat) {
                        case "RDF/XML":
                            model.write(out, RDFLanguages.RDFXML.getLabel());
                            result_json_ld = out.toString(StandardCharsets.UTF_8);
                            break;
                        case "N-triples":
                            model.write(out, RDFLanguages.NTRIPLES.getLabel());
                            result_json_ld = out.toString(StandardCharsets.UTF_8);
                            break;
                        case "Turtle":
                            model.write(out, RDFLanguages.TURTLE.getLabel());
                            result_json_ld = out.toString(StandardCharsets.UTF_8);
                            break;
                        default:
                            model.write(out, RDFLanguages.JSONLD.getLabel());
                            result_json_ld = out.toString(StandardCharsets.UTF_8);
                            break;
                    }

                } else {
                    result_json_ld = "No JSON-LD data was found.";
                }

            } else {
                result_json_ld = "No search for JSON-LD data was done.";
            }

        model1.addAttribute("result_turtle", result_turtle);
        model1.addAttribute("result_rdfa", result_rdfa);
        model1.addAttribute("result_json_ld", result_json_ld);
        model1.addAttribute("result_microdata", result_microdata);

        System.out.println("This is RDFa: " + result_rdfa);
        System.out.println("This is Turtle:" + result_turtle);
        System.out.println("This is JSON-LD:"+ result_json_ld);
        System.out.println("This is Microdata: "+ result_microdata);

        return "display-data";
    }


    @GetMapping("/getDataFromHtml")
    public String getDataFromHtml(String html, @RequestParam String [] formats,
                          Model model1) throws IOException, JSONException {

        String apiMicrodata = "http://127.0.0.1:2000/resultFromHtmlMicrodata";
        String apiJson = "http://127.0.0.1:2000/resultFromHtmlJson";
        String apiRdfa = "http://127.0.0.1:2000/resultFromHtmlRdfa";

        RestTemplate restTemplate = new RestTemplate();
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        JSONObject JsonObject = new JSONObject();
        JsonObject.put("html", html);


        final ObjectMapper objectMapper = new ObjectMapper();
        HttpEntity<String> request =
                new HttpEntity<String>(JsonObject.toString(), headers);

        String res1 = restTemplate.postForObject(apiMicrodata, request, String.class);
        String res2 = restTemplate.postForObject(apiJson, request, String.class);
        String res3 = restTemplate.postForObject(apiRdfa, request, String.class);

        String result_microdata = "No search for Microdata was done";
        String result_turtle = "No Turtle data was found.";
        String result_rdfa = "No search for RDFa was done";
        String result_json_ld = "No search for JSON-LD was done";

        if(Arrays.asList(formats).contains("Microdata")) {
            if (res1 != null && !res1.equals("[]")) {
                result_microdata = res1;
            } else if (res1.equals("[]")) {
                result_microdata = "Microdata was not found";
            }
        }

        if(Arrays.asList(formats).contains("JSON-LD")) {
            if (res2 != null && !res2.equals("[]")) {
                result_json_ld = res2;
            } else if (res2.equals("[]")) {
                result_json_ld = "JSON-LD was not found";
            }
        }

        if(Arrays.asList(formats).contains("RDFa")) {
            if (res3 != null && !res3.equals("[]")) {
                result_rdfa = res3;
            } else if (res3.equals("[]")) {
                result_rdfa = "RDFa was not found";
            }
        }

        model1.addAttribute("result_turtle", result_turtle);
        model1.addAttribute("result_rdfa", result_rdfa);
        model1.addAttribute("result_json_ld", result_json_ld);
        model1.addAttribute("result_microdata", result_microdata);

        return "display-data";
    }

    }

