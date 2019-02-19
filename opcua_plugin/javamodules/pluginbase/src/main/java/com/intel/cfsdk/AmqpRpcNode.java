package com.intel.cfsdk;

import java.io.IOException;
import java.util.concurrent.TimeoutException;

import com.rabbitmq.client.*;
import com.intel.cfsdk.PluginConfiguration;

import java.net.URISyntaxException;

import net.sf.json.JSONObject;
import net.sf.json.JSONException;

import com.intel.cfsdk.RpcNode;
import com.intel.cfsdk.PluginRpcImpl;

public class AmqpRpcNode implements RpcNode {
    private Connection connection;
    private Channel channel;
    private ConnectionFactory factory = null;
    private PluginRpcImpl rpcCallback;
    private String name;
    private String uri;

    public AmqpRpcNode(String name, String uri) {
        this.name = name;
        this.uri = uri;
    }

    public void setUri (String uri) throws IOException {
        try {
            this.uri = uri;
            this.factory.setUri(uri);
        } catch (Exception e){
            e.printStackTrace();
        }
    }

    public void connect() throws IOException {
        this.factory = new ConnectionFactory();
        try {
            this.factory.setUri(this.uri);
            this.factory.setAutomaticRecoveryEnabled(true);
            this.factory.setNetworkRecoveryInterval(10000);
        } catch (Exception e){
            e.printStackTrace();
        }
        try {
            this.connection = this.factory.newConnection();
            this.channel = this.connection.createChannel();
            this.subscribe();
            System.out.println("amqp connected");
        } catch (Exception e) {
            //Thread.sleep(5000);
            e.printStackTrace();
        }
    }

    public void disconnect() throws IOException, TimeoutException {
        if (this.channel != null) {
            try {
                this.channel.close();
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        if (this.connection != null) {
            try {
                this.connection.close();
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    public void publish(String devName, JSONObject data) throws IOException, TimeoutException {
        if (this.channel != null) {
            this.channel.basicPublish("",devName,
                new AMQP.BasicProperties.Builder()
                .contentType("application/json")
                .deliveryMode(2)
                .priority(1)
                .build(),
                data.toString().getBytes());
        }
    }

    private void subscribe() {
        String queueName = null;
        boolean autoAck = false;
        try {
            //this.channel.exchangeDeclare(this.name, "direct", true);
            //queueName = this.channel.queueDeclare().getQueue();
            queueName = this.channel.queueDeclare().getQueue();
            //this.channel.queueBind(queueName, this.name, "");
            this.channel.queueDeclare(this.name, false, false,false, null);
            this.channel.queuePurge(this.name);
            this.channel.basicQos(100);
            //this.channel.queueBind(this.name, this.name, "");
        } catch (IOException e){
            e.printStackTrace();
        }
        Consumer consumer = new DefaultConsumer(this.channel) {
            @Override
            public void handleDelivery(String consumerTag, Envelope envelope,
                    AMQP.BasicProperties properties, byte[]body) throws IOException {
                String message = new String(body, "UTF-8");
                String routingKey = envelope.getRoutingKey();
                String contentType = properties.getContentType();
                long deliveryTag = envelope.getDeliveryTag();
                channel.basicAck(deliveryTag, false);
            }
        };
        Consumer requester = new DefaultConsumer(this.channel) {
			@Override
            public void handleDelivery(String consumerTag, Envelope envelope,
                    AMQP.BasicProperties properties, byte[]body) throws IOException {
                String message = new String(body, "UTF-8");
                String routingKey = envelope.getRoutingKey();
                String contentType = properties.getContentType();
                long deliveryTag = envelope.getDeliveryTag();
                /*process mesage*/
                String replyTo = properties.getReplyTo();
                if(replyTo != null){
                    String jsonOut = null;
                    try{
                        jsonOut = rpcCallback.pluginRpcReceiver(JSONObject.fromObject(message)).toString();
                    } catch (JSONException e){
                        e.printStackTrace();
                    }
                    channel.basicPublish("",replyTo,
                        new AMQP.BasicProperties.Builder()
                            .correlationId(properties.getCorrelationId())
                            .contentType("application/json")
                            .build(),
                            jsonOut.getBytes());
                }
                channel.basicAck(deliveryTag, false);
            }
        };
        try {
            this.channel.basicConsume(queueName, false, consumer);
            this.channel.basicConsume(this.name, false, requester);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public void setCallback(PluginRpcImpl callback){
        this.rpcCallback = callback;
    }


    public void destroy() {
        if (this.channel != null) {
            try {
                this.channel.close();
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
        if (this.connection != null) {
            try {
                this.connection.close();
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }
}
