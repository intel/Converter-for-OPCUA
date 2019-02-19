package com.intel.cfsdk;

import java.util.*;
import java.util.regex.*;
import java.io.*;

public class PluginConfig {
    private BufferedReader bufferedReader;

    public PluginConfig(String file){
        try{
            load(file);
        } catch (IOException e){
            e.printStackTrace();
        }
    }

    public boolean load(String file) throws IOException {
        bufferedReader = new BufferedReader(new FileReader(file));
        return true;
    }

    public String ReadItemValue(String section, String variable, String defaultValue) throws IOException {
        String strLine, value = "";
        boolean isInSection;
        try {
            while ((strLine = bufferedReader.readLine()) != null) {
            	isInSection = false;
                strLine = strLine.trim();
                strLine = strLine.split("[;]")[0];
                Pattern p;
                Matcher m;
                p = Pattern.compile("\\[\\w+]");
                m = p.matcher((strLine));
                if (m.matches()) {
                    p = Pattern.compile("\\[" + section + "\\]");
                    m = p.matcher(strLine);
                    if (m.matches()) {
                        isInSection = true;
                    } else {
                        isInSection = false;
                    }
                }
                if (isInSection = true) {
                    strLine = strLine.trim();
                    String[] strArray = strLine.split("=");
                    if (strArray.length == 1) {
                        value = strArray[0].trim();
                        if (value.equalsIgnoreCase(variable)) {
                            value = "";
                            return value;
                        }
                    } else if (strArray.length == 2) {
                        value = strArray[0].trim();
                        if (value.equalsIgnoreCase(variable)) {
                            value = strArray[1].trim();
                            return value;
                        }
                    } else if (strArray.length > 2) {
                        value = strArray[0].trim();
                        if (value.equalsIgnoreCase(variable)) {
                            value = strLine.substring(strLine.indexOf("=") + 1).trim();
                            return value;
                        }
                    }
                }
            }
        } finally {
            if(bufferedReader != null){
            	try {
            		bufferedReader.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }
        return defaultValue;
    }
}
