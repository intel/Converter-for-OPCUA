package com.intel.cfsdk.plugin.modbus;

import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStreamReader;

import net.sf.json.JSONArray;
import net.sf.json.JSONObject;

import com.intel.cfsdk.PluginClient;
import com.intel.cfsdk.Node;
import com.intel.cfsdk.plugin.modbus.ModbusPluginEntity;
import com.intel.cfsdk.plugin.modbus.ModbusPluginConfig;
import com.intel.cfsdk.PluginRpcImpl;

public class PluginMain extends PluginClient {
    private ModbusPluginEntity devices;
    private PluginRpcImpl pluginRpcImpl;
    private JSONObject deviceClient;
    private JSONArray clients;

    public PluginMain(ModbusPluginEntity entity, ModbusPluginConfig config){
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

    @Override
    public JSONObject rpcReceiver(JSONObject jsonIn){
        System.out.println(jsonIn.toString());
        return super.rpcReceiver(jsonIn);
    }

    public static void main( String[] args )
    {
        if (args.length < 1) {
            System.out.println("usage: plugin_main <plugin folder>");
            return;
        }
        ModbusPluginEntity pluginEntity = new ModbusPluginEntity(args[0]);
        ModbusPluginConfig pluginConfig = new ModbusPluginConfig(args[1]);
        PluginMain pluginClient = new PluginMain(pluginEntity, pluginConfig);
        pluginClient.registerRpc();
        pluginClient.start(true);
    }
}
