/*
 * Provides classes for representing and working with tree-of-life data.
 */
 
// Maps tree-of-life node names to node objects
export type TolMap = Map<string, TolNode>;
// Represents a tree-of-life node
export class TolNode {
	children: string[];
	parent: string | null;
	tips: number;
	pSupport: boolean;
	imgName: null | string;
	commonName: null | string;
	constructor(children: string[] = [], parent = null, tips = 0, pSupport = false){
		this.children = children;
		this.parent = parent;
		this.tips = tips;
		this.pSupport = pSupport;
		this.imgName = null;
		this.commonName = null;
	}
}
