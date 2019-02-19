package com.intel.cfsdk;

import com.intel.cfsdk.PluginRpcInterface;
import com.intel.cfsdk.PluginClient;
import net.sf.json.JSONObject;

public class PluginRpcImpl implements PluginRpcInterface {
    private PluginClient client;
    public PluginRpcImpl(PluginClient client){
        this.client = client;
    }

    public JSONObject pluginRpcReceiver(JSONObject jsonIn){
        return this.client.rpcReceiver(jsonIn);
    }

    public void pluginRpcNotify(JSONObject jsonIn){
    	System.out.println("\n" + jsonIn);
    }
}
