/*
 * Contains classes used for representing tree-of-life data, and tile-based layouts of such data.
 *
 * Generally, given a TolNode with child TolNodes representing tree-of-life T,
 * a LayoutTree is created for a subtree of T, and represents a tile-based layout of that subtree.
 * The LayoutTree holds LayoutNodes, each of which holds placement info for a linked TolNode.
 */

//represents a tree-of-life node/tree
export class TolNode {
	name: string;
	children: TolNode[];
	constructor(name: string, children: TolNode[] = []){
		this.name = name;
		this.children = children;
	}
}
//represents a tree of LayoutNode objects, and has methods for (re)computing layout
export class LayoutTree {
	root: LayoutNode;
	options: LayoutOptions;
	//creates an object representing a TolNode tree, up to a given depth (0 means just the root)
	constructor(tol: TolNode, options: LayoutOptions, depth: number){
		this.root = this.initHelper(tol, depth);
		this.options = options;
	}
	//used by constructor to initialise the LayoutNode tree
	initHelper(tolNode: TolNode, depth: number): LayoutNode {
		if (depth == 0){
			return new LayoutNode(tolNode, []);
		} else {
			let children = tolNode.children.map((n: TolNode) => this.initHelper(n, depth-1));
			let node = new LayoutNode(tolNode, children);
			children.forEach(n => n.parent = node);
			return node;
		}
	}
	//attempts layout of TolNode tree, for an area with given xy-coordinate and width+height (in pixels)
	tryLayout(pos: [number,number], dims: [number,number]){
		//create a new LayoutNode tree, keeping the old tree in case of failure
		let newLayout: LayoutNode | null;
		switch (this.options.layoutType){
			case 'sqr':   newLayout =   sqrLayoutFn(this.root, pos, dims, true, this.options); break;
			case 'rect':  newLayout =  rectLayoutFn(this.root, pos, dims, true, this.options); break;
			case 'sweep': newLayout = sweepLayoutFn(this.root, pos, dims, true, this.options); break;
		}
		if (newLayout == null){
			return false;
		}
		this.copyTreeForRender(newLayout, this.root);
		return true;
	}
	//attempts layout after adding a node's children to the LayoutNode tree
	tryLayoutOnExpand(pos: [number,number], dims: [number,number], node: LayoutNode){
		//add children
		node.children = node.tolNode.children.map((n: TolNode) => new LayoutNode(n, []));
		node.children.forEach(n => n.parent = node);
		this.updateDCounts(node, node.children.length-1);
		//try layout
		let success = this.tryLayout(pos, dims);
		if (!success){ //remove children
			node.children = [];
			this.updateDCounts(node, -node.tolNode.children.length+1);
		}
		return success;
	}
	//attempts layout after removing a node's children from the LayoutNode tree
	tryLayoutOnCollapse(pos: [number,number], dims: [number,number], node: LayoutNode){
		//remove children
		let children = node.children;
		node.children = [];
		this.updateDCounts(node, -children.length+1);
		//try layout
		let success = this.tryLayout(pos, dims);
		if (!success){ //add children
			node.children = children;
			this.updateDCounts(node, node.children.length-1);
		}
		return success;
	}
	//used to copy a new LayoutNode tree's render-relevant data to the old tree
	copyTreeForRender(node: LayoutNode, target: LayoutNode): void {
		target.pos = node.pos;
		target.dims = node.dims;
		target.showHeader = node.showHeader;
		target.sepSweptArea = node.sepSweptArea;
		//these are currently redundant, but maintain data-consistency
		target.dCount = node.dCount;
		target.empSpc = node.empSpc;
		//recurse on children
		node.children.forEach((n,i) => this.copyTreeForRender(n, target.children[i]));
	}
	//used to update a LayoutNode tree's dCount fields after adding/removing a node's children
	updateDCounts(node: LayoutNode | null, diff: number): void{
		while (node != null){
			node.dCount += diff;
			node = node.parent;
		}
	}
}
//contains settings that affect how layout is done
export type LayoutOptions = {
	tileSpacing: number; //spacing between tiles, in pixels (ignoring borders)
	headerSz: number;
	minTileSz: number; //minimum size of a tile edge, in pixels (ignoring borders)
	maxTileSz: number;
	layoutType: 'sqr' | 'rect' | 'sweep'; //the LayoutFn function to use
	rectMode: 'horz' | 'vert' | 'linear' | 'auto'; //layout in 1 row, 1 column, 1 row or column, or multiple rows
	sweepMode: 'left' | 'top' | 'shorter' | 'auto'; //sweep to left, top, shorter-side, or to minimise empty space
	sweptNodesPrio: 'linear' | 'sqrt' | 'sqrt-when-high'; //specifies allocation of space to swept-vs-remaining nodes
	sweepingToParent: boolean; //allow swept nodes to occupy empty space in a parent's swept-leaves area
};
//represents a node/tree, and holds layout data for a TolNode node/tree
export class LayoutNode {
	tolNode: TolNode;
	children: LayoutNode[];
	parent: LayoutNode | null;
	//used for rendering a corresponding tile
	pos: [number, number];
	dims: [number, number];
	showHeader: boolean;
	sepSweptArea: SepSweptArea | null;
	//used for layout heuristics
	dCount: number; //number of descendant leaf nodes
	empSpc: number; //amount of unused space (in pixels)
	//creates object with given fields ('parent' is generally initialised later, 'dCount' is computed)
	constructor(
		tolNode: TolNode, children: LayoutNode[], pos=[0,0] as [number,number], dims=[0,0] as [number,number],
		{showHeader=false, sepSweptArea=null as SepSweptArea|null, empSpc=0} = {}){
		this.tolNode = tolNode;
		this.children = children;
		this.parent = null;
		this.pos = pos;
		this.dims = dims;
		this.showHeader = showHeader;
		this.sepSweptArea = sepSweptArea;
		this.dCount = children.length == 0 ? 1 : children.map(n => n.dCount).reduce((x,y) => x+y);
		this.empSpc = empSpc;
	}
}
//used with layout option 'sweepingToParent', and represents, for a LayoutNode, a parent area to place leaf nodes in
export class SepSweptArea {
	pos: [number, number];
	dims: [number, number];
	sweptLeft: boolean; //true if the parent's leaves were swept left
	constructor(pos: [number, number], dims: [number, number], sweptLeft: boolean){
		this.pos = pos;
		this.dims = dims;
		this.sweptLeft = sweptLeft;
	}
	clone(): SepSweptArea {
		return new SepSweptArea([...this.pos], [...this.dims], this.sweptLeft);
	}
}

//type for functions called by LayoutTree to perform layout
//returns a new LayoutNode tree for a given LayoutNode's TolNode tree, or null if layout was unsuccessful
type LayoutFn = (
	node: LayoutNode,
	pos: [number, number],
	dims: [number, number],
	showHeader: boolean,
	opts: LayoutOptions,
	ownOpts?: {
		subLayoutFn?: LayoutFn,
		sepAreaInfo?: {avail: SepSweptArea, usedLen: number}|null,
	},
) => LayoutNode | null;
//lays out nodes as squares in a rectangle, with spacing
let sqrLayoutFn: LayoutFn = function (node, pos, dims, showHeader, opts){
	if (node.children.length == 0){
		let tileSz = Math.min(dims[0], dims[1], opts.maxTileSz);
		if (tileSz < opts.minTileSz)
			return null;
		return new LayoutNode(node.tolNode, [], pos, [tileSz,tileSz]);
	}
	//get number-of-columns with lowest leftover empty space
	let headerSz = showHeader ? opts.headerSz : 0;
	let availW = dims[0] - opts.tileSpacing, availH = dims[1] - headerSz - opts.tileSpacing;
	if (availW*availH <= 0)
		return null;
	let numChildren = node.children.length, ar = availW/availH;
	let minOuterEmp = Number.POSITIVE_INFINITY, numCols = 0, numRows = 0, tileSize = 0;
	for (let nc = 1; nc <= numChildren; nc++){
		let nr = Math.ceil(numChildren/nc);
		let ar2 = nc/nr;
		let frac = ar > ar2 ? ar2/ar : ar/ar2;
		let tileSz = ar > ar2 ? availH/nr-opts.tileSpacing : availW/nc-opts.tileSpacing;
		if (tileSz < opts.minTileSz)
			continue;
		else if (tileSz > opts.maxTileSz)
			tileSz = opts.maxTileSz;
		let empSpc = (1-frac)*availW*availH + (nc*nr-numChildren)*(tileSz - opts.tileSpacing)**2;
		if (empSpc < minOuterEmp){
			minOuterEmp = empSpc;
			numCols = nc;
			numRows = nr;
			tileSize = tileSz;
		}
	}
	if (minOuterEmp == Number.POSITIVE_INFINITY)
		return null;
	//get child layouts
	let childLayouts: LayoutNode[] = new Array(numChildren);
	let empSpc = (numCols*numRows-numChildren)*(tileSize-opts.tileSpacing)**2;
	for (let i = 0; i < numChildren; i++){
		let child = node.children[i];
		let childX = opts.tileSpacing + (i % numCols)*(tileSize + opts.tileSpacing);
		let childY = opts.tileSpacing + headerSz + Math.floor(i / numCols)*(tileSize + opts.tileSpacing);
		let lyt = sqrLayoutFn(child, [childX,childY], [tileSize,tileSize], true, opts);
		if (lyt == null)
			return null;
		childLayouts[i] = lyt;
		empSpc += childLayouts[i].empSpc;
	}
	let newNode = new LayoutNode(node.tolNode, childLayouts, pos,
		[numCols * (tileSize + opts.tileSpacing) + opts.tileSpacing,
			numRows * (tileSize + opts.tileSpacing) + opts.tileSpacing + headerSz],
		{showHeader, empSpc});
	childLayouts.forEach(n => n.parent = newNode);
	return newNode;
}
//lays out nodes as rectangles organised into rows, partially using other layouts for children
let rectLayoutFn: LayoutFn = function (node, pos, dims, showHeader, opts, ownOpts={subLayoutFn: rectLayoutFn}){
	if (node.children.every(n => n.children.length == 0))
		return sqrLayoutFn(node, pos, dims, showHeader, opts);
	//find grid-arrangement with lowest leftover empty space
	let headerSz = showHeader ? opts.headerSz : 0;
	let availW = dims[0] - opts.tileSpacing, availH = dims[1] - opts.tileSpacing - headerSz;
	let numChildren = node.children.length;
	let rowBrks: number[]|null = null; //will holds node indices at which each row starts
	let lowestTotalEmp = Number.POSITIVE_INFINITY, rowBreaks = null, childLayouts = null;
	let minEmpHorz = 0, lastEmpVert = 0;
	rowBrksLoop:
	while (true){
		//update rowBrks or exit loop
		if (rowBrks == null){
			if (opts.rectMode == 'vert'){
				rowBrks = seq(numChildren);
			} else {
				rowBrks = [0];
			}
		} else {
			if (opts.rectMode == 'horz' || opts.rectMode == 'vert'){
				break rowBrksLoop;
			} else if (opts.rectMode == 'linear'){
				if (rowBrks.length == 1 && numChildren > 1){
					rowBrks = seq(numChildren);
				} else {
					break rowBrksLoop;
				}
			} else {
				let i = rowBrks.length-1;
				while (true){
					if (i > 0 && rowBrks[i] < numChildren-1 - (rowBrks.length-1 - i)){
						rowBrks[i]++;
						break;
					} else if (i > 0){
						i--;
					} else {
						if (rowBrks.length < numChildren){
							rowBrks = seq(rowBrks.length+1);
						} else {
							break rowBrksLoop;
						}
						break;
					}
				}
			}
		}
		//create list-of-lists representing each row's cells' dCounts
		let rowsOfCnts: number[][] = new Array(rowBrks.length).fill([]);
		for (let r = 0; r < rowBrks.length; r++){
			let numNodes = (r == rowBrks.length-1) ? numChildren-rowBrks[r] : rowBrks[r+1]-rowBrks[r];
			let rowNodeIdxs = seq(numNodes).map(i => i+rowBrks![r]);
			rowsOfCnts[r] = rowNodeIdxs.map(idx => node.children[idx].dCount);
		}
		//get cell dims
		let totalTileCount = node.children.map(n => n.dCount).reduce((x,y) => x+y);
		let cellHs = rowsOfCnts.map(row => row.reduce((x,y) => x+y) / totalTileCount * availH);
		let cellWs: number[] = new Array(numChildren);
		for (let r = 0; r < rowsOfCnts.length; r++){
			let rowCount = rowsOfCnts[r].reduce((x,y) => x+y);
			for (let c = 0; c < rowsOfCnts[r].length; c++){
				cellWs[rowBrks[r]+c] = rowsOfCnts[r][c] / rowCount * availW;
			}
		}
		//impose min-tile-size
		cellHs = limitVals(cellHs, opts.minTileSz, Number.POSITIVE_INFINITY)!;
		if (cellHs == null)
			continue rowBrksLoop;
		for (let r = 0; r < rowsOfCnts.length; r++){
			let temp = limitVals(cellWs.slice(rowBrks[r], rowBrks[r] + rowsOfCnts[r].length),
				opts.minTileSz, Number.POSITIVE_INFINITY);
			if (temp == null)
				continue rowBrksLoop;
			cellWs.splice(rowBrks[r], rowsOfCnts[r].length, ...temp);
		}
		//get cell x/y coords
		let cellXs: number[] = new Array(cellWs.length).fill(0);
		for (let r = 0; r < rowBrks.length; r++){
			for (let c = 1; c < rowsOfCnts[r].length; c++){
				let nodeIdx = rowBrks[r]+c;
				cellXs[nodeIdx] = cellXs[nodeIdx-1] + cellWs[nodeIdx-1];
			}
		}
		let cellYs: number[] = new Array(cellHs.length).fill(0);
		for (let r = 1; r < rowBrks.length; r++){
			cellYs[r] = cellYs[r-1] + cellHs[r-1];
		}
		//get child layouts and empty-space
		let childLyts: LayoutNode[] = new Array(numChildren);
		let minEmpH = Number.POSITIVE_INFINITY, lastEmpV = 0, empSpc = 0;
		for (let r = 0; r < rowBrks.length; r++){
			let minEmpVert = Number.POSITIVE_INFINITY;
			for (let c = 0; c < rowsOfCnts[r].length; c++){
				let nodeIdx = rowBrks[r]+c;
				let child = node.children[nodeIdx];
				let childX = cellXs[nodeIdx] + opts.tileSpacing, childY = cellYs[r] + opts.tileSpacing + headerSz,
					childW = cellWs[nodeIdx] - opts.tileSpacing, childH = cellHs[r] - opts.tileSpacing;
				let newChild: LayoutNode | null = null;
				if (child.children.length == 0){
					let contentSz = Math.min(childW, childH, opts.maxTileSz);
					newChild = new LayoutNode(child.tolNode, [], [childX,childY], [contentSz,contentSz]);
				} else if (child.children.every(n => n.children.length == 0)){
					newChild = sqrLayoutFn(child, [childX,childY], [childW,childH], true, opts);
				} else {
					let layoutFn = (ownOpts && ownOpts.subLayoutFn) || rectLayoutFn;
					newChild = layoutFn(child, [childX,childY], [childW,childH], true, opts);
				}
				if (newChild == null)
					continue rowBrksLoop;
				childLyts[nodeIdx] = newChild;
				empSpc += newChild.empSpc + (childW*childH)-(newChild.dims[0]*newChild.dims[1]);
				//handle horizontal empty-space-shifting
				let empHorz = childW - newChild.dims[0];
				if (c < rowsOfCnts[r].length-1){
					cellXs[nodeIdx+1] -= empHorz;
					cellWs[nodeIdx+1] += empHorz;
					empSpc -= empHorz * childH;
				} else {
					minEmpH = Math.min(minEmpH, empHorz);
				}
				//other updates
				minEmpVert = Math.min(childH-newChild.dims[1], minEmpVert);
			}
			//handle vertical empty-space-shifting
			if (r < rowBrks.length-1){
				cellYs[r+1] -= minEmpVert;
				cellHs[r+1] += minEmpVert;
				empSpc -= minEmpVert * availW;
			} else {
				lastEmpV = minEmpVert;
			}
		}
		//check with best-so-far
		if (empSpc < lowestTotalEmp){
			lowestTotalEmp = empSpc;
			rowBreaks = [...rowBrks];
			childLayouts = childLyts;
			minEmpHorz = minEmpH;
			lastEmpVert = lastEmpV;
		}
	}
	if (rowBreaks == null || childLayouts == null) //redundant hinting for tsc
		return null;
	//determine layout
	let newDims: [number,number] = [dims[0]-minEmpHorz, dims[1]-lastEmpVert];
	let newNode = new LayoutNode(node.tolNode, childLayouts, pos, newDims,
		{showHeader, empSpc: lowestTotalEmp - (availW*availH - newDims[0]*newDims[1])});
	childLayouts.forEach(n => n.parent = newNode);
	return newNode;
}
//lays out nodes by pushing leaves to one side, partially using other layouts for children
let sweepLayoutFn: LayoutFn = function (node, pos, dims, showHeader, opts, ownOpts={sepAreaInfo: null}){
	//separate leaf and non-leaf nodes
	let leaves: LayoutNode[] = [], nonLeaves: LayoutNode[] = [];
	node.children.forEach(n => (n.children.length == 0 ? leaves : nonLeaves).push(n));
	//determine layout
	let tempTree: LayoutNode;
	if (nonLeaves.length == 0){
		return sqrLayoutFn(node, pos, dims, showHeader, opts);
	} else if (leaves.length == 0){
		return rectLayoutFn(node, pos, dims, showHeader, opts, {subLayoutFn:sweepLayoutFn});
	} else {
		let ratio: number, numNonLeaves = nonLeaves.map(n => n.dCount).reduce((x,y) => x+y);
		if (opts.sweptNodesPrio == 'linear'){
			ratio = leaves.length / (leaves.length + numNonLeaves);
		} else if (opts.sweptNodesPrio == 'sqrt'){
			ratio = Math.sqrt(leaves.length) / (Math.sqrt(leaves.length) + Math.sqrt(numNonLeaves));
		} else {
			ratio = (leaves.length < nonLeaves.length) ?
				leaves.length / (leaves.length + numNonLeaves) :
				Math.sqrt(leaves.length) / (Math.sqrt(leaves.length) + Math.sqrt(numNonLeaves));
		}
		//
		let headerSz = showHeader ? opts.headerSz : 0;
		let sweptLayout = null, nonLeavesLayout = null, sweptLeft = false;
		//get swept-area layout
		let usedParentArea = null, usingParentArea = false;
		let sepAreaInfo: {avail: SepSweptArea, usedLen: number}|null = null;
		if (opts.sweepingToParent && ownOpts.sepAreaInfo){
			let parentArea = ownOpts.sepAreaInfo.avail;
			usedParentArea = ownOpts.sepAreaInfo.avail.clone();
			tempTree = new LayoutNode(new TolNode('SWEEP_' + node.tolNode.name), leaves);
				//not updating the children to point to tempTree as a parent seems acceptable here
			sweptLeft = parentArea.sweptLeft;
			sweptLayout = sqrLayoutFn(tempTree, [0,0], parentArea.dims, !sweptLeft, opts);
			if (sweptLayout != null){
				//move leaves to parent area
				sweptLayout.children.map(n => {
					n.pos[0] += parentArea!.pos[0];
					n.pos[1] += parentArea!.pos[1];
				});
				//update sepAreaInfo
				if (sweptLeft){
					parentArea.pos[1] += sweptLayout.dims[1] - opts.tileSpacing - headerSz;
					parentArea.dims[1] = Math.max(0, parentArea.dims[1] - sweptLayout.dims[1] - opts.tileSpacing*2);
				} else {
					parentArea.pos[0] += sweptLayout.dims[0] - opts.tileSpacing;
					parentArea.pos[1] += headerSz;
					parentArea.dims[0] = Math.max(0, parentArea.dims[0] - sweptLayout.dims[0] - opts.tileSpacing*2);
					parentArea.dims[1] += -headerSz;
				}
				//get remaining-area layout
				let newDims: [number,number] = [dims[0], dims[1] - (sweptLeft ? headerSz : 0)];
				tempTree = new LayoutNode(new TolNode('SWEEP_REM_' + node.tolNode.name), nonLeaves);
				if (nonLeaves.length > 1){
					nonLeavesLayout = rectLayoutFn(tempTree, [0,0], newDims, false, opts, {subLayoutFn: sweepLayoutFn});
				} else {
					nonLeavesLayout = rectLayoutFn(tempTree, [0,0], newDims, false, opts,
						{subLayoutFn: (n,p,d,h,o) => sweepLayoutFn(n,p,d,h,o,{sepAreaInfo:ownOpts.sepAreaInfo})});
				}
				if (nonLeavesLayout != null){
					nonLeavesLayout.children.forEach(layout => {layout.pos[1] += (sweptLeft ? headerSz : 0)});
					//
					ownOpts.sepAreaInfo.usedLen += sweptLeft ? sweptLayout.dims[1] : sweptLayout.dims[0];
					let usedLen = ownOpts.sepAreaInfo.usedLen;
					if (sweptLeft){
						usedParentArea.dims[1] = usedLen;
						if (usedParentArea.pos[1] + usedLen > nonLeavesLayout.dims[1] + headerSz){
							nonLeavesLayout.dims[1] = usedParentArea.pos[1] + usedLen - headerSz
						} else {
							usedParentArea.dims[1] = nonLeavesLayout.dims[1] + headerSz - usedParentArea.pos[1];
						}
						usedParentArea.dims[0] -= opts.tileSpacing;
					} else {
						usedParentArea.dims[0] = usedLen;
						if (usedParentArea.pos[0] + usedLen > nonLeavesLayout.dims[0]){
							nonLeavesLayout.dims[0] = usedParentArea.pos[0] + usedLen;
						} else {
							usedParentArea.dims[0] = nonLeavesLayout.dims[0] - usedParentArea.pos[0];
						}
						usedParentArea.dims[1] -= opts.tileSpacing;
					}
					usingParentArea = true;
				}
			}
		}
		if (!usingParentArea){
			let newDims: [number,number] = [dims[0], dims[1]-headerSz];
			tempTree = new LayoutNode(new TolNode('SWEEP_' + node.tolNode.name), leaves);
			let xyChg: [number,number];
			//get swept-area layout
			let leftLayout = null, topLayout = null;
			let documentAR = document.documentElement.clientWidth / document.documentElement.clientHeight;
			if (opts.sweepMode=='left' || (opts.sweepMode=='shorter' && documentAR >= 1) || opts.sweepMode=='auto'){
				leftLayout = sqrLayoutFn(tempTree, [0,0],
					[Math.max(newDims[0]*ratio, opts.minTileSz+opts.tileSpacing*2), newDims[1]], false, opts);
			}
			if (opts.sweepMode=='top' || (opts.sweepMode=='shorter' && documentAR < 1) || opts.sweepMode=='auto'){
				topLayout = sqrLayoutFn(tempTree, [0,0],
					[newDims[0], Math.max(newDims[1]*ratio, opts.minTileSz+opts.tileSpacing*2)], false, opts);
			}
			if (opts.sweepMode == 'auto'){
				sweptLayout =
					(leftLayout && topLayout && ((leftLayout.empSpc < topLayout.empSpc) ? leftLayout : topLayout)) ||
					leftLayout || topLayout;
			} else {
				sweptLayout = leftLayout || topLayout;
			}
			sweptLeft = (sweptLayout == leftLayout);
			if (sweptLayout == null)
				return null;
			sweptLayout.children.forEach(layout => {layout.pos[1] += headerSz});
			//get remaining-area layout
			if (sweptLeft){
				xyChg = [sweptLayout.dims[0] - opts.tileSpacing, 0];
				newDims[0] += -sweptLayout.dims[0] + opts.tileSpacing;
			} else {
				xyChg = [0, sweptLayout.dims[1] - opts.tileSpacing];
				newDims[1] += -sweptLayout.dims[1] + opts.tileSpacing;
			}
			tempTree = new LayoutNode(new TolNode('SWEEP_REM_' + node.tolNode.name), nonLeaves);
			if (nonLeaves.length > 1){
				nonLeavesLayout = rectLayoutFn(tempTree, [0,0], newDims, false, opts, {subLayoutFn:sweepLayoutFn});
			} else {
				//get leftover swept-layout-area to propagate
				if (sweptLeft){
					sepAreaInfo = {
						avail: new SepSweptArea( //pos is relative to the non-leaves-area
							[-sweptLayout.dims[0]+opts.tileSpacing, sweptLayout.dims[1]-opts.tileSpacing],
							[sweptLayout.dims[0], Math.max(0, newDims[1]-sweptLayout.dims[1]-opts.tileSpacing*2)],
							sweptLeft),
						usedLen: 0
					};
				} else {
					sepAreaInfo = {
						avail: new SepSweptArea(
							[sweptLayout.dims[0]-opts.tileSpacing, -sweptLayout.dims[1]+opts.tileSpacing],
							[Math.max(0, newDims[0]-sweptLayout.dims[0]-opts.tileSpacing*2), sweptLayout.dims[1]],
							sweptLeft),
						usedLen: 0
					};
				}
				//generate layout
				nonLeavesLayout = rectLayoutFn(tempTree, [0,0], newDims, false, opts,
					{subLayoutFn: (n,p,d,h,o) => sweepLayoutFn(n,p,d,h,o,{sepAreaInfo:sepAreaInfo})});
			}
			if (nonLeavesLayout == null)
				return null;
			nonLeavesLayout.children.forEach(layout => {
				layout.pos[0] += xyChg[0];
				layout.pos[1] += xyChg[1] + headerSz;
			});
		}
		if (sweptLayout == null || nonLeavesLayout == null) //hint for tsc
			return null;
		//return combined layouts
		let children = leaves.concat(nonLeaves);
		let layouts = sweptLayout.children.concat(nonLeavesLayout.children);
		let layoutsInOldOrder = seq(node.children.length)
			.map(i => children.findIndex(n => n == node.children[i]))
			.map(i => layouts[i]);
		let newDims: [number,number] = (usingParentArea ?
			[nonLeavesLayout.dims[0], nonLeavesLayout.dims[1] + (sweptLeft ? headerSz : 0)] :
			(sweptLeft ?
				[sweptLayout.dims[0] + nonLeavesLayout.dims[0] - opts.tileSpacing,
					Math.max(sweptLayout.dims[1]-(sepAreaInfo ? sepAreaInfo.usedLen : 0),
						nonLeavesLayout.dims[1]) + headerSz] :
				[Math.max(sweptLayout.dims[0]-(sepAreaInfo ? sepAreaInfo.usedLen : 0), nonLeavesLayout.dims[0]),
					sweptLayout.dims[1] + nonLeavesLayout.dims[1] - opts.tileSpacing + headerSz]));
		let empSpc = (usingParentArea ? 0 : sweptLayout.empSpc) + nonLeavesLayout.empSpc;
		let newNode = new LayoutNode(node.tolNode, layoutsInOldOrder, pos, newDims,
			{showHeader, empSpc, sepSweptArea: usingParentArea ? usedParentArea : null});
		layoutsInOldOrder.forEach(n => n.parent = newNode);
		return newNode;
	}
}

//clips values in array to within [min,max], and redistributes to compensate, returning null if unable
function limitVals(arr: number[], min: number, max: number): number[]|null {
	let vals = [...arr];
	let clipped: boolean[] = new Array(vals.length).fill(false);
	let owedChg = 0;
	while (true){
		for (let i = 0; i < vals.length; i++){
			if (clipped[i])
				continue;
			if (vals[i] < min){
				owedChg += vals[i] - min;
				vals[i] = min;
				clipped[i] = true;
			} else if (vals[i] > max){
				owedChg += vals[i] - max;
				vals[i] = max;
				clipped[i] = true;
			}
		}
		if (Math.abs(owedChg) < Number.EPSILON)
			return vals;
		let indicesToUpdate;
		if (owedChg > 0){
			indicesToUpdate = vals.reduce(
				(arr: number[], n, i) => {if (n < max) arr.push(i); return arr;},
				[]);
		} else {
			indicesToUpdate = vals.reduce(
				(arr: number[], n, i) => {if (n > min) arr.push(i); return arr;},
				[]);
		}
		if (indicesToUpdate.length == 0)
			return null;
		for (let i of indicesToUpdate){
			vals[i] += owedChg / indicesToUpdate.length;
		}
		owedChg = 0;
	}
}
function seq(len: number){ //returns [0, ..., len]
	return [...Array(len).keys()];
}
