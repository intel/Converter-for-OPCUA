package com.intel.cfsdk.plugin.mqtt;

import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.Random;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;

import org.eclipse.paho.client.mqttv3.MqttAsyncClient;
import org.eclipse.paho.client.mqttv3.MqttCallback;
import org.eclipse.paho.client.mqttv3.MqttClient;
import org.eclipse.paho.client.mqttv3.MqttConnectOptions;
import org.eclipse.paho.client.mqttv3.MqttDeliveryToken;
import org.eclipse.paho.client.mqttv3.MqttException;
import org.eclipse.paho.client.mqttv3.MqttMessage;
import org.eclipse.paho.client.mqttv3.MqttPersistenceException;
import org.eclipse.paho.client.mqttv3.MqttSecurityException;
import org.eclipse.paho.client.mqttv3.MqttTopic;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;

import net.sf.json.JSONArray;
import net.sf.json.JSONObject;

import com.intel.cfsdk.PluginClient;
import com.intel.cfsdk.Node;
import com.intel.cfsdk.plugin.mqtt.MqttPluginEntity;
import com.intel.cfsdk.plugin.mqtt.MqttPluginConfig;
import com.intel.cfsdk.PluginRpcImpl;

public class PluginMain extends PluginClient{
    private MqttPluginEntity devices;
    private PluginRpcImpl pluginRpcImpl;
    private JSONObject deviceClient;
    private JSONArray clients;
    private List<Map<String, Object>> deviceClients;

    public PluginMain(MqttPluginEntity entity, MqttPluginConfig config){
        super(entity, config);
        this.devices = entity;
        this.pluginRpcImpl = new PluginRpcImpl(this);
    }

    @Override
    public void registerRpc(){
        super.rpcNode.setCallback(this.pluginRpcImpl);
        try {
            super.rpcNode.connect();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
    
    public void pluginPoll(){
    	try {
			super.pubEvent("", "online", "");
		} catch (Exception e) {
			e.printStackTrace();
		}
    }
    
    public void mqtt_message(String topic,String msg){
    	for(int i = 0; i < this.deviceClients.size(); i++){
			Map<String, Object> map = this.deviceClients.get(i);
			Node blobTopic = ((Node) map.get("device")).getChild("Blob Topic");
			if(blobTopic != null && topic.equals(blobTopic.value)){
				System.out.println(blobTopic.value);
			}else{
				Node node = this.devices.getNodeByVal(topic, (Node)map.get("device"));
				if(node != null){
					Node pairNode = node.getPairFriend();
					try {
						super.pubData((String) map.get("name"), pairNode.name, msg);
					} catch (Exception e) {
						e.printStackTrace();
					}
				}
			}
    	}
    }
    
    public void mqtt_connect_sub(Map<String,Object> mapClient){
    	MqttClient mqttClient = (MqttClient) mapClient.get("client");
    	if(mqttClient.isConnected()){
    		Node cDevice = (Node) mapClient.get("device");
        	Node rawTopic = cDevice.getChild("Raw Topic");
        	if(rawTopic != null){
        		try {
    				mqttClient.subscribe(rawTopic.value, 1);
    			} catch (MqttException e) {
    				e.printStackTrace();
    			}
        	}
        	Node alamTopic = cDevice.getChild("Alam Topic");
        	if(alamTopic != null){
        		try {
    				mqttClient.subscribe(alamTopic.value, 1);
    			} catch (MqttException e) {
    				e.printStackTrace();
    			}
        	}
        	Node blobTopic = cDevice.getChild("Blob Topic");
        	if(blobTopic != null){
        		try {
    				mqttClient.subscribe(blobTopic.value, 1);
    			} catch (MqttException e) {
    				e.printStackTrace();
    			}
        	}
        	System.out.println("mqtt plugin connected the broker:" + mapClient.get("name"));
    	}
    }
    
    public void mqtt_connect(Map<String,Object> mapClient){
    	System.out.println("mqtt plugin connecting the broker......");
    	MqttClient mqttClient = null;
    	Properties props = null;
    	String clientId = MqttClient.generateClientId();
    	String ip = (String) mapClient.get("ip");
    	String path = this.getClass().getResource("").getPath();
    	path = path.split(":")[1];
    	path = path.substring(0, path.indexOf("!"));
    	path = path.substring(0, path.lastIndexOf("/")); 
    	//System.out.println(path);
    	String cafile = path + "/" + (String) mapClient.get("cafile");
    	String cert = path + "/" + (String) mapClient.get("cert");
    	String key = path + "/" + (String) mapClient.get("key");
    	
    	try {
    		mqttClient = new MqttClient(ip,clientId,new MemoryPersistence());
		} catch (MqttException e) {
			e.printStackTrace();
		}
    	MqttConnectOptions options = new MqttConnectOptions();
    	if((String) mapClient.get("cafile") != null){
    		if(new File(cafile).exists() && new File(cert).exists() && new File(key).exists()){
    			props.setProperty("cafile", cafile);
            	props.setProperty("cert", cert);
            	props.setProperty("key", key);
            	options.setSSLProperties(props);
    		}
    	}
    	options.setCleanSession(false);
    	options.setConnectionTimeout(10);
    	options.setKeepAliveInterval(20);
    	mqttClient.setCallback(new PushCallback(){
			public void messageArrived(String topic, MqttMessage message){
				String msg = new String(message.getPayload());
				System.out.println("message:" + msg);
				mqtt_message(topic,msg);
			}
		});
    	try {
    		mqttClient.connect(options);
    		Thread.sleep(1000);
		} catch (Exception e) {
			System.out.println("mqtt plugin connected the broker " + mapClient.get("name") + ":" + mqttClient.isConnected());
		}
    	mapClient.put("client", mqttClient);
    	mqtt_connect_sub(mapClient);
    }
    
    public void mqtt_disconnect(Map<String,Object> mapClient){
    	if(mapClient.get("client") != null){
    		Node cDevice = (Node) mapClient.get("device");
        	Node rawTopic = cDevice.getChild("Raw Topic");
        	if(rawTopic != null){
        		try {
        			((MqttClient) mapClient.get("client")).unsubscribe(rawTopic.value);
    			} catch (MqttException e) {
    				e.printStackTrace();
    			}
        	}
        	Node alamTopic = cDevice.getChild("Alam Topic");
        	if(alamTopic != null){
        		try {
        			((MqttClient) mapClient.get("client")).unsubscribe(alamTopic.value);
    			} catch (MqttException e) {
    				e.printStackTrace();
    			}
        	}
        	Node blobTopic = cDevice.getChild("Blob Topic");
        	if(blobTopic != null){
        		try {
        			((MqttClient) mapClient.get("client")).unsubscribe(blobTopic.value);
    			} catch (MqttException e) {
    				e.printStackTrace();
    			}
        	}
    	}
    	try {
			((MqttClient) mapClient.get("client")).disconnect();
		} catch (MqttException e) {
			e.printStackTrace();
		}
    	System.out.println("mqtt plugin disconnected the broker:" + mapClient.get("name"));
    }
    
    public Map<String,Object> getCli(String name){
    	if(name != null){
    		for(int i = 0; i < this.deviceClients.size(); i++){
    			Map<String, Object> map = this.deviceClients.get(i);
    			if(name.equals((String)map.get("name"))){
    				return map;
    			}
        	}
    	}
    	return null;
    }
    
    public JSONObject send(String name,String topic,String msg){
    	int errorcode = 0;
    	String result = null;
    	Map<String,Object> map = this.getCli(name);
    	if(map != null){
    		if(((MqttClient)map.get("client")).isConnected()){
    			try {
					((MqttClient)map.get("client")).publish(topic, msg.getBytes(), 1, false);
					errorcode = 0;
					result = "successed to send data";
				} catch (Exception e) {
					errorcode = 1;
					result = "failed to send data";
				}
    		}else{
    			errorcode = 1;
				result = "failed to send data";
    		}
    	}else{
    		errorcode = 1;
			result = "failed to send data";
    	}
    	Map<String, Object> res = new HashMap<String, Object>();
    	res.put("code", errorcode);
    	res.put("data", result);
    	return JSONObject.fromObject(res);
    }
    
    public void restart(String name){
    	Map<String,Object> map = this.getCli(name);
    	if(map != null){
    		this.mqtt_connect(map);
			this.mqtt_disconnect(map);
    	}else{
    		this.cli_stop();
    		this.cli_start();
    	}
    }
    
    public List<JSONObject> get_client_status(String name){
    	List<Map<String, Object>> list = new ArrayList<Map<String, Object>>();
    	Map<String, Object> listMap = new HashMap<String, Object>();
    	List<JSONObject> json = new ArrayList<JSONObject>();
    	Map<String,Object> map = this.getCli(name);
    	if(map != null){
    		list.add(map);
    	}else{
    		list = this.deviceClients;
    	}
    	for(int i = 0; i < list.size(); i++){
    		String cname = (String) list.get(i).get("name");
    		Boolean connected = ((MqttClient) list.get(i).get("client")).isConnected();
    		String ip = (String) list.get(i).get("ip");
    		listMap.put("name", cname);
    		listMap.put("connected", connected);
    		listMap.put("ip", ip);
    		json.add(JSONObject.fromObject(listMap));
    	}
    	return json;
    }
    
    public void cli_stop(){
    	for(int i = 0; i < this.deviceClients.size(); i++){
			Map<String, Object> map = this.deviceClients.get(i);
			this.mqtt_disconnect(map);
    	}
    }
    
    public void cli_start(){
    	List<Node> mqtt_devices = this.devices.getCustomNodes();
    	String ip, host, port, cafile, cert, key;
    	this.deviceClients = new ArrayList<Map<String, Object>>();
    	for(int i = 0; i < mqtt_devices.size(); i++){
    		Map<String, Object> mapClient = new HashMap<String, Object>();
    		MqttClient mqttClient = null;
    		Node device = mqtt_devices.get(i);
    		Node broker = device.getChild("MQTT Broker");
    		if(broker == null){
    			continue;
    		}
    		JSONObject broker_value = JSONObject.fromObject(broker.value);
    		if(broker_value.containsKey("host")){
    			host = broker_value.getString("host");
    		}else{
    			host = "127.0.0.1";
    		}
    		if(broker_value.containsKey("port")){
    			port = broker_value.getString("port");
    		}else{
    			port = "1883";
    		}
    		if(broker_value.containsKey("cafile")){
    			cafile = broker_value.getString("cafile");
    		}else{
    			cafile = null;
    		}
    		if(broker_value.containsKey("cert")){
    			cert = broker_value.getString("cert");
    		}else{
    			cert = null;
    		}
    		if(broker_value.containsKey("key")){
    			key = broker_value.getString("key");
    		}else{
    			key = null;
    		}
    		ip = "tcp://" + host + ":" + port;
    		mapClient.put("name", device.name);
    		mapClient.put("ip", ip);
    		mapClient.put("cafile", cafile);
    		mapClient.put("cert", cert);
    		mapClient.put("key", key);
    		mapClient.put("client", mqttClient);
    		mapClient.put("device", device);
    		this.deviceClients.add(mapClient);
    	}
    	for(int i=0;i<this.deviceClients.size();i++){
    		try {
				mqtt_connect(this.deviceClients.get(i));
			} catch (Exception e) {
				e.printStackTrace();
			}
    	}
    }
    
    public static void main( String[] args )
    {
        if (args.length < 1) {
            System.out.println("parameter error");
            return;
        }
        MqttPluginEntity pluginEntity = new MqttPluginEntity(args[0]);
        MqttPluginConfig pluginConfig = new MqttPluginConfig(args[1]);
        PluginMain pluginClient = new PluginMain(pluginEntity, pluginConfig);
        pluginClient.registerRpc();
        pluginClient.start(true);
        pluginClient.cli_start();
    }
}
