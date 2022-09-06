package com.example.vbsproject.service;

import org.apache.jena.base.Sys;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.util.logging.Logger;

@Service
public class FileExportImpl implements FileExport{

    private static final String EXPORT_DIRECTORY = "E:\\intellijProjects\\vbs-project\\src\\main\\resources";

    @Override
    public Path export(String fileContent, String fileName) {

        Path filePath = Paths.get(EXPORT_DIRECTORY, fileName);
        try {
            Path exportedFilePath = Files.write(filePath, fileContent.getBytes(), StandardOpenOption.CREATE);
            return exportedFilePath;
        } catch (IOException e) {
            System.out.println(e.toString());
        }

        return null;
    }
}
