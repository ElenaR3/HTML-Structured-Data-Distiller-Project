package com.example.vbsproject.service;

import java.nio.file.Path;

public interface FileExport {

    public Path export(String fileContent, String fileName);

}
