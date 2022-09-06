package com.example.vbsproject;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.servlet.ServletComponentScan;

@SpringBootApplication
@ServletComponentScan
public class VbsProjectApplication {

    public static void main(String[] args) {
        SpringApplication.run(VbsProjectApplication.class, args);
    }

}
