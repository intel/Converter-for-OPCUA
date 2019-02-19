package com.intel.cfsdk;

public enum NodeType {
    UnKnown(0),
    Folder(1),
    Variable(2),
    Property(3),
    Method(4),
    Object(5),
    CustomObj(6);
    private int nType;

    private NodeType(int _nType) {
        this.nType = _nType;
    }
}
