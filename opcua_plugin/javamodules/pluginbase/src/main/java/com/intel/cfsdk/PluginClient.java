package com.intel.cfsdk;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.Set;

import net.sf.json.JSONArray;
import net.sf.json.JSONObject;
import net.sf.json.JSONException;

import java.io.IOException;

import com.intel.cfsdk.AmqpRpcNode;
import com.intel.cfsdk.PluginConfig;
import com.intel.cfsdk.ReturnCodes;
import com.intel.cfsdk.PluginRpcImpl;

public class PluginClient implements Runnable {
    final public String name;
    final public AmqpRpcNode rpcNode;
    private PluginEntity entity;
    private PluginConfig config;
    private Map<String, Method>methods;
    private Thread monitor;
    private boolean bLive;
    private final String default_amqp_url = "amqp://guest:guest@127.0.0.1";
    private String url;

    public PluginClient(PluginEntity entity, PluginConfig config) {
        this.config = config;
        this.entity = entity;
        this.name = this.entity.pluginName;
        this.bLive = false;
        this.methods = this.entity.getMethods();
        try {
			this.url = this.config.ReadItemValue("Amqp", "url", default_amqp_url);
		} catch (IOException e) {
			e.printStackTrace();
		}
        this.rpcNode = new AmqpRpcNode(this.name, this.url);
    }

    public void registerRpc(){
        this.rpcNode.setCallback(new PluginRpcImpl(this));
        try {
            this.rpcNode.connect();
        } catch (IOException e){
            e.printStackTrace();
        }
    }

    public void pluginPoll(){
        List<Node> customObjTypes = this.entity.getCustomNodes();
        if((customObjTypes == null)||(customObjTypes.size() == 0)){
            try{
                this.pubEvent("","online","");
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        else{
            for(int loop=0; loop<customObjTypes.size();loop++){
                try{
                    this.pubEvent(customObjTypes.get(loop).name, "online", "");
                } catch (Exception e){
                    e.printStackTrace();
                }
            }
        }
    }

    public void run() {
        System.out.println("Running "+ this.name);
        while (this.isAlive()){
            try{
                this.pluginPoll();
                Thread.sleep(5000);
            } catch (InterruptedException e) {
                System.out.println("Thread "+ this.name +" interrupted.");
            }
        }
        System.out.println("Thread "+ this.name+" exiting");
    }

    public void start(boolean daemon){
        System.out.println("Starting "+this.name);
        if (this.monitor == null){
            this.bLive = true;
            this.monitor = new Thread(this, this.name);
            this.monitor.start();
        }
    }

    public void stop(){
        this.bLive=false;
        try{
            this.pubEvent("","exit","");
        }catch(Exception e){
            e.printStackTrace();
        }
        try{
            this.rpcNode.disconnect();
        }catch(Exception e){
            e.printStackTrace();
        }
    }

    public boolean isAlive() {
        return this.bLive;
    }

    public void pubData(String dev_name, String var_name, String var_data) throws Exception {
        Map<String, Object> map = new HashMap<String, Object>();
        List list = new ArrayList();
        list.add(this.name);
        list.add(dev_name);
        list.add(var_name);
        list.add(var_data);
        map.put("data", list);
        JSONObject json_out = JSONObject.fromObject(map);
        try {
            this.rpcNode.publish("opcua", json_out);
        } catch (Exception e) {
            e.printStackTrace();
        }
    } 

    public void pubEvent(String dev_name, String evt_name, String evt_data) throws Exception { 
        Map<String, Object> map = new HashMap<String, Object>();
        List list = new ArrayList();
        list.add(this.name);
        list.add(dev_name);
        list.add(evt_name);
        list.add(evt_data);
        map.put("event", list);
        JSONObject json_out = JSONObject.fromObject(map);
        try {
            this.rpcNode.publish("opcua", json_out);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    public JSONObject getrd() {
        Map<String, Object> map = new HashMap<String, Object>();
        map.put("code", ReturnCodes.Good.getValue());
        String temp = this.entity.data.toString();
        map.put("data", temp);
        return JSONObject.fromObject(map);
    }

    public JSONObject ping() {
        Map<String, Object> map = new HashMap<String, Object>();
        map.put("code", ReturnCodes.Good.getValue());
        map.put("data", "\"pong\"");
        return JSONObject.fromObject(map);
    }

    public String getstate() {
        Map<String, Object> map = new HashMap<String, Object>();
        map.put("code", ReturnCodes.PLUGIN_ParamError.getValue());
        map.put("data", "\"No yet implemented in this Plugin\"");
        return map.toString();
    }

    public String refresh() {
        Map<String, Object> map = new HashMap<String, Object>();
        map.put("code", ReturnCodes.PLUGIN_ParamError.getValue());
        map.put("data", "\"No yet implemented in this Plugin\"");
        return map.toString();
    }

    public JSONObject rpcReceiver(JSONObject jsonIn){
        String method = null;
        JSONObject out=null;
        if(jsonIn.containsKey("method")){
            try {
                method = jsonIn.getString("method");
            } catch (JSONException e){
                Map<String, Object> map = new HashMap<String, Object>();
                System.out.println(ReturnCodes.PLUGIN_ParamError.getValue());
                map.put("code", ReturnCodes.PLUGIN_ParamError.getValue());
                map.put("data", "\"no method string is included\"");
                System.out.println(map.toString());
                out = JSONObject.fromObject(map);
                return out;
            }
            if("getrd".equals(method)){
                try {
                    out = this.getrd();
                } catch (JSONException e){
                    Map<String, Object> map = new HashMap<String, Object>();
                    map.put("code", ReturnCodes.PLUGIN_ParamError.getValue());
                    map.put("data", "wrong method return string");
                    out = JSONObject.fromObject(map);
                    return out;
                }
                return out;
            } else if ("ping".equals(method)) {
                try {
                    out = this.ping();
                } catch (JSONException e){
                    Map<String, Object> map = new HashMap<String, Object>();
                    map.put("code", ReturnCodes.PLUGIN_ParamError.getValue());
                    map.put("data", "wrong method return string");
                    out = JSONObject.fromObject(map);
                    return out;
                }
                return out;
            }
        }
        else{
            Map<String, Object> map = new HashMap<String, Object>();
            map.put("code", ReturnCodes.PLUGIN_ParamError);
            map.put("data", "\"no method string is included\"");
            out = JSONObject.fromObject(map.toString());
        }
        return out; 
    }
}
