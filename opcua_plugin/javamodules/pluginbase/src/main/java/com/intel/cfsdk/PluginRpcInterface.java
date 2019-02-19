package com.intel.cfsdk;

import net.sf.json.JSONObject;

public interface PluginRpcInterface {
    JSONObject pluginRpcReceiver(JSONObject jsonIn);
    void pluginRpcNotify(JSONObject jsonIn);
}
