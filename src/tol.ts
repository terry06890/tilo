/*
 * Provides classes for representing and working with tree-of-life data.
 */
 
// Represents a tree-of-life node/tree
export class TolNode {
	name: string;
	children: TolNode[];
	parent: TolNode | null;
	constructor(name: string, children: TolNode[] = [], parent = null){
		this.name = name;
		this.children = children;
		this.parent = parent;
	}
}
// Represents a tree-of-life node obtained from tolData.json
export class TolNodeRaw {
	name: string;
	children?: TolNodeRaw[];
	constructor(name: string, children: TolNodeRaw[] = []){
		this.name = name;
		this.children = children;
	}
}
// Converts a TolNodeRaw tree to a TolNode tree
export function tolFromRaw(node: TolNodeRaw): TolNode {
	function helper(node: TolNodeRaw, parent: TolNode | null){
		let tolNode = new TolNode(node.name);
		if (node.children == null){
			tolNode.children = [];
		} else {
			tolNode.children = node.children.map(child => helper(child, tolNode));
		}
		tolNode.parent = parent;
		return tolNode;
	}
	return helper(node, null);
}
// Returns a map from TolNode names to TolNodes in a given tree
export function getTolMap(tolTree: TolNode): Map<string, TolNode> {
	function helper(node: TolNode, map: Map<string, TolNode>){
		map.set(node.name, node);
		node.children.forEach(child => helper(child, map));
	}
	let map = new Map();
	helper(tolTree, map);
	return map;
}
