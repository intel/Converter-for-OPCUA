package com.intel.cfsdk;

import java.io.IOException;
import net.sf.json.JSONObject;
import java.util.concurrent.TimeoutException;

public interface RpcNode {
    public void connect() throws IOException;
    public void setUri (String uri) throws IOException;
    public void disconnect() throws IOException, TimeoutException;
    public void publish(String devName, JSONObject data) throws IOException, TimeoutException;
    public void destroy();
}
