package com.intel.cfsdk;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import com.intel.cfsdk.PluginConfig;

import java.io.IOException;

//import net.sf.json.JSONArray;

public class PluginConfiguration {
    private final String default_log_level="info";
    private final String default_security_tls = "false";
    private final String default_amqp_url = "amqp://guest:guest@127.0.0.1";

    private PluginConfig pluginConfig;

    public void builder(String file) {
        try {
            pluginConfig.load(file);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public String GetAmqpUri() {
        try {
            return pluginConfig.ReadItemValue("Amqp", "url", default_amqp_url);
        } catch (IOException e) {
            e.printStackTrace();
        }
        return null;
    }
}
