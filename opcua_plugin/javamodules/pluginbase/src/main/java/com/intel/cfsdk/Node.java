package com.intel.cfsdk;

import java.util.List;
import java.util.ArrayList;
import com.intel.cfsdk.NodeType;

public class Node {
    public String name;
    public NodeType type;
    public String value;
    public Node parent;
    public Node pairfriend;
    public List<Node> children = new ArrayList<Node>();

    public Node(String name, Node object, NodeType type, String value) {
        this.name = name;
        this.type = type;
        this.value = value;
        this.parent = null;
        this.pairfriend = null;
        
        if(object != null) {
            List<Node> list = object.getChildren();
            for(int loop = 0; loop < list.size(); loop++) {
                this.addChild(list.get(loop));
            }

        }
    }

    public Node getParent() {
        return this.parent;
    }

    public Node addChild(Node node) {
        for (int loop = 0; loop < this.children.size(); loop++) {
            Node uNode = this.children.get(loop);
            if (uNode.name.equals(node.name)) {
                return uNode;    
            }
        }
        node.parent = this;
        this.children.add(node);
        return node;
    }

    public List<Node> getChildren() {
        return this.children;
    }

    public Node getChild(String name) {
        for (int loop = 0; loop < this.children.size(); loop++) {
            Node uNode = this.children.get(loop);
            if (uNode.name.equals(name)) {
                return uNode;    
            }
        }
        return null;
    }

    public void addPairFriend(Node node) {
        this.pairfriend = node;
    }

    public Node getPairFriend() {
        return this.pairfriend;
    }
}
