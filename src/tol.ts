/*
 * Types for representing tree-of-life data
 */

// Represents a tree-of-life node
export class TolNode {
	otolId: string | null;
	children: string[];
	parent: string | null;
	tips: number;
	pSupport: boolean; // Indicates phylogenetic support
	commonName: null | string;
	imgName: null | string |
		[string, string] | [null, string] | [string, null]; // Pairs represent compound images
	constructor(children: string[] = [], parent = null, tips = 0, pSupport = false){
		this.otolId = null;
		this.children = children;
		this.parent = parent;
		this.tips = tips;
		this.pSupport = pSupport;
		this.commonName = null;
		this.imgName = null;
	}
}
// Maps TolNode names to TolNode objects
export type TolMap = Map<string, TolNode>;
