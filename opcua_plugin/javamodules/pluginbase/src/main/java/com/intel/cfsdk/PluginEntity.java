package com.intel.cfsdk;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.Set;

import net.sf.json.JSONArray;
import net.sf.json.JSONObject;
import net.sf.json.JSONException;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.*;

import com.intel.cfsdk.Node;
import com.intel.cfsdk.Method;

public class PluginEntity {
    public JSONObject data;

    private Node rootNode;
    private List<Node> customObjTypes = new ArrayList<Node>();
    private List<Node> customNodes = new ArrayList<Node>();
    public  String pluginName;
    private String topicName;
    private String jsonContext;
    private Map<String, Method> nodeMethods = new HashMap<String, Method>();
    private Map<String, Method> apiMethods = new HashMap<String, Method>();

    private String fileName;

    
    private Map<String, Object> map = new HashMap<String, Object>(); 

    public PluginEntity(String file) {
        this.fileName = new String(file);
        this.rootNode = null;
        this.jsonLoads(this.fileName);
    }

    private void addApiMethod(String funcName, JSONArray inputs, JSONArray outputs) {
        this.apiMethods.put(funcName, new Method(funcName, inputs, outputs));
    }

    public Map<String, Method> getMethods(){
        return this.nodeMethods;
    }

    private void parseApi() {
        JSONObject object = (JSONObject)this.data.get("user_data");
        JSONArray array = JSONArray.fromObject(object.get("apilist"));
        List<JSONObject> apiList;
        for ( int loop = 0; loop < array.size(); loop++) {
            JSONArray ins = null;
            JSONObject apiObject;
            try {
                apiObject = array.getJSONObject(loop);
                if(apiObject.containsKey("input")){
                    ins = apiObject.getJSONArray("input");
                }
                else{
                    ins = null;
                }
                if(apiObject.containsKey("output")){
                    this.addApiMethod(apiObject.getString("name"), ins, apiObject.getJSONArray("output"));
                }
                else{
                    this.addApiMethod(apiObject.getString("name"), ins, null);
                }
            } catch (JSONException e) {
                e.printStackTrace();
            }
        }
    }

    public void addMethod(String funcName, JSONArray inputs, JSONArray outputs){
        this.nodeMethods.put(funcName, new Method(funcName, inputs, outputs));
    }

    private void parseNode(Node parent, JSONObject nodeData){
        if(nodeData.containsKey("methods")){
            try {
                JSONArray methods = nodeData.getJSONArray("methods");
                for (int loop=0; loop<methods.size();loop++) {
                    JSONArray ins=null;
                    JSONObject obj = methods.getJSONObject(loop);
                    if(obj.containsKey("input")){
                        ins = obj.getJSONArray("input");
                    }
                    this.addMethod(obj.getString("name"), ins, obj.getJSONArray("output"));
                }
            } catch (JSONException e){
                e.printStackTrace();
            }
        }
        if(nodeData.containsKey("folders")){
            try {
                JSONArray folders = nodeData.getJSONArray("folders");
                for (int loop=0; loop<folders.size();loop++) {
                    JSONObject obj = folders.getJSONObject(loop);
                    Node node = parent.addChild(new Node(obj.getString("name"), null, NodeType.Folder, null));
                    this.parseNode(node, obj);
                }
            } catch (JSONException e){
                e.printStackTrace();
            }
        }
        if(nodeData.containsKey("objects")){
            try {
                JSONArray objects = nodeData.getJSONArray("objects");
                for (int loop=0; loop<objects.size();loop++) {
                    JSONObject obj = objects.getJSONObject(loop);
                    Node node = parent.addChild(new Node(obj.getString("name"), null, NodeType.Object, null));
                    this.parseNode(node, obj);
                }
            } catch (JSONException e){
                e.printStackTrace();
            }
        }
        if(nodeData.containsKey("variables")){
            try {
                JSONArray variables = nodeData.getJSONArray("variables");
                for (int loop=0; loop<variables.size();loop++) {
                    JSONObject varObj = variables.getJSONObject(loop);
                    Node node = parent.addChild(new Node(varObj.getString("name"), null, NodeType.Variable, null));
                }
            } catch (JSONException e){
                e.printStackTrace();
            }
        }
        if(nodeData.containsKey("properties")){
            try {
                JSONArray properties = nodeData.getJSONArray("properties");
                for (int loop=0; loop<properties.size();loop++) {
                    JSONObject propObj = properties.getJSONObject(loop);
                    String val = null;
                    if(propObj.containsKey("value")){
                        val = propObj.getString("value");
                    }
                    Node node = parent.addChild(new Node(propObj.getString("name"), null, NodeType.Property, val));
                    if(propObj.containsKey("refs")){
                        val = propObj.getString("refs");
                        Node friend = parent.getChild(val);
                        node.addPairFriend(friend);
                    }
                    parent.addChild(node);
                }
            } catch (JSONException e){
                e.printStackTrace();
            }
        }
        for (int loop=0; loop<this.customObjTypes.size();loop++){
            if(nodeData.containsKey(this.customObjTypes.get(loop).name)){
                try {
                    JSONArray cNodes = nodeData.getJSONArray(this.customObjTypes.get(loop).name);
                    for (int j=0; j<cNodes.size(); j++) {
                        JSONObject cNode = cNodes.getJSONObject(j);
                        Node newNode = new Node(cNode.getString("name"), this.customObjTypes.get(loop), NodeType.CustomObj,null);
                        this.parseNode(newNode, cNode);
                        this.customNodes.add(newNode);
                        parent.addChild(newNode);
                    }
                } catch (JSONException e) {
                    e.printStackTrace();
                }
            }
        }
    }

    private Node getNodeByVal(Node node, String value) {
        if(value.equals(node.value)){
            return node;
        }
        List<Node> children = node.getChildren();
        for (int loop=0; loop < children.size(); loop++){
            node = this.getNodeByVal(children.get(loop), value);
            if(node != null){
                return node;
            }
        }
        return null;
    }

    private Node getNodeByType(Node node, NodeType type){
        if(node.type==type){
            return node;
        }
        List<Node> children = node.getChildren();
        for (int loop=0; loop<children.size(); loop++) {
            node = this.getNodeByType(children.get(loop), type);
            if(node !=null){
                return node;
            }
        }
        return null;
    }

    public List<Node> getChildrenByType(Node parent, NodeType type) {
        List<Node> nodes=new ArrayList<Node>();
        List<Node> children = parent.getChildren();
        for(int loop=0; loop<children.size();loop++){
            Node uNode = children.get(loop);
            if(uNode.type==type){
                nodes.add(uNode);
            }
        }
        return nodes;
    }

    public Node getProperty(Node node, String name){
        List<Node> children = node.getChildren();
        for(int loop=0; loop<children.size(); loop++){
            Node uNode = children.get(loop);
            if(uNode.type==NodeType.Property){
                if(uNode.name == name){
                    return uNode;
                }
            }
        }
        return null;
    }

    public Node getNodeByVal(String value, Node parent){
        if(parent == null){
            parent = this.rootNode;
        }
        return this.getNodeByVal(parent,value);
    }

    public List<Node> getCustomNodes(){
        return this.customNodes;
    }

    private void jsonLoads(String jsonfile) {
        BufferedReader reader = null;
        try {
            FileInputStream fileInputStream = new FileInputStream(jsonfile);
            InputStreamReader inputStreamReader = new InputStreamReader(fileInputStream,"UTF-8");
            reader = new BufferedReader(inputStreamReader);
            String tempString = null;
            while ((tempString = reader.readLine()) != null) {
                if(this.jsonContext == null){
                    this.jsonContext = tempString;
                }
                else{
                    this.jsonContext += tempString;
                }
            }
            reader.close();
        } catch(IOException e){
            e.printStackTrace();
        } finally {
            if (reader != null) {
                try {
                    reader.close();
                } catch (IOException e) {
                    e.printStackTrace();
                }
            }
        }
        this.data = JSONObject.fromObject(this.jsonContext);
        try {
            // System.out.println(this.data);
            JSONObject object = this.data.getJSONObject("user_data");
            this.topicName = object.getString("topic");
            this.pluginName = this.topicName.split("/")[1];
            this.parseApi();
            JSONObject opcuaObj = (JSONObject)object.get("opcua");
            if (opcuaObj.containsKey("custom_types")) {
                JSONArray customTypes = opcuaObj.getJSONArray("custom_types");
                for (int loop=0; loop < customTypes.size(); loop++){
                    JSONObject customObj;
                    customObj = customTypes.getJSONObject(loop);
                    Node node = new Node(customObj.getString("name"),null,NodeType.CustomObj,null);
                    this.parseNode(node,customObj);
                    this.customObjTypes.add(node);
                }
            }
            if (opcuaObj.containsKey("folders")){
                JSONArray folderArray = opcuaObj.getJSONArray("folders");
                JSONObject folder0 = folderArray.getJSONObject(0);
                this.rootNode = new Node(folder0.getString("name"),null,NodeType.Folder,null);
                this.parseNode(this.rootNode, folder0);
            }
        } catch (JSONException e) {
                e.printStackTrace();
        }
    }
}

