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
		let oldDCount = node.dCount;
		let children = node.children;
		node.children = [];
		this.updateDCounts(node, -oldDCount + 1);
		//try layout
		let success = this.tryLayout(pos, dims);
		if (!success){ //add children
			node.children = children;
			this.updateDCounts(node, oldDCount - 1);
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
	sweptNodesPrio: 'linear' | 'sqrt' | 'pow-2/3'; //specifies allocation of space to swept-vs-remaining nodes
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
		this.dCount = children.length == 0 ? 1 : arraySum(children.map(n => n.dCount));
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
	//these return a new LayoutNode tree for a given LayoutNode's TolNode tree, or null if layout was unsuccessful
type LayoutFn = (
	node: LayoutNode,
	pos: [number, number],
	dims: [number, number],
	showHeader: boolean,
	opts: LayoutOptions,
	ownOpts?: any,
) => LayoutNode | null;
//lays out node as one square, ignoring child nodes (used for base cases)
let oneSqrLayoutFn: LayoutFn = function (node, pos, dims, showHeader, opts){
	let tileSz = Math.min(dims[0], dims[1], opts.maxTileSz);
	if (tileSz < opts.minTileSz){
		return null;
	}
	return new LayoutNode(node.tolNode, [], pos, [tileSz,tileSz]);
}
//lays out nodes as squares within a grid with intervening+surrounding spacing
let sqrLayoutFn: LayoutFn = function (node, pos, dims, showHeader, opts){
	if (node.children.length == 0){
		return oneSqrLayoutFn(node, pos, dims, false, opts);
	}
	//consider area excluding header and top/left spacing
	let headerSz = showHeader ? opts.headerSz : 0;
	let newPos = [opts.tileSpacing, opts.tileSpacing + headerSz];
	let newDims = [dims[0] - opts.tileSpacing, dims[1] - opts.tileSpacing - headerSz];
	if (newDims[0] * newDims[1] <= 0){
		return null;
	}
	//find number of rows/columns with least empty space
	let numChildren = node.children.length;
	let areaAR = newDims[0] / newDims[1]; //aspect ratio
	let lowestEmpSpc = Number.POSITIVE_INFINITY, usedNumCols = 0, usedNumRows = 0, usedTileSz = 0;
	for (let numCols = 1; numCols <= numChildren; numCols++){
		let numRows = Math.ceil(numChildren / numCols);
		let gridAR = numCols / numRows;
		let usedFrac = //fraction of area occupied by maximally-fitting grid
			areaAR > gridAR ? gridAR / areaAR : areaAR / gridAR;
		//get tile edge length
		let tileSz = (areaAR > gridAR ? newDims[1] / numRows : newDims[0] / numCols) - opts.tileSpacing;
		if (tileSz < opts.minTileSz){
			continue;
		} else if (tileSz > opts.maxTileSz) {
			tileSz = opts.maxTileSz;
		}
		//get empty space
		let empSpc = (1 - usedFrac) * (newDims[0] * newDims[1]) + //area outside grid plus
			(numCols * numRows - numChildren) * (tileSz - opts.tileSpacing)**2; //empty cells within grid
		//compare with best-so-far
		if (empSpc < lowestEmpSpc){
			lowestEmpSpc = empSpc;
			usedNumCols = numCols;
			usedNumRows = numRows;
			usedTileSz = tileSz;
		}
	}
	if (lowestEmpSpc == Number.POSITIVE_INFINITY){
		return null;
	}
	//get child layouts
	let childLayouts: LayoutNode[] = new Array(numChildren);
	for (let i = 0; i < numChildren; i++){
		let child = node.children[i];
		let childX = newPos[0] + (i % usedNumCols) * (usedTileSz + opts.tileSpacing);
		let childY = newPos[1] + Math.floor(i / usedNumCols) * (usedTileSz + opts.tileSpacing);
		if (child.children.length == 0){
			let lyt = oneSqrLayoutFn(node, [childX,childY], [usedTileSz,usedTileSz], false, opts);
			childLayouts[i] = lyt!;
		} else {
			let lyt = sqrLayoutFn(child, [childX,childY], [usedTileSz,usedTileSz], true, opts);
			if (lyt == null){
				return null;
			}
			childLayouts[i] = lyt;
		}
	}
	//create layout
	let usedDims: [number, number] = [
		usedNumCols * (usedTileSz + opts.tileSpacing) + opts.tileSpacing,
		usedNumRows * (usedTileSz + opts.tileSpacing) + opts.tileSpacing + headerSz,
	];
	let empSpc = //empty space within usedDims area
		(usedNumCols * usedNumRows - numChildren) * (usedTileSz - opts.tileSpacing)**2 + 
		arraySum(childLayouts.map(lyt => lyt.empSpc));
	let newNode = new LayoutNode(node.tolNode, childLayouts, pos, usedDims, {showHeader, empSpc});
	childLayouts.forEach(n => n.parent = newNode);
	return newNode;
}
//lays out nodes as rows of rectangles, deferring to sqrLayoutFn() or oneSqrLayoutFn() for simpler cases
	//'subLayoutFn' allows other LayoutFns to use this layout, but transfer control back to themselves on recursion
let rectLayoutFn: LayoutFn = function (node, pos, dims, showHeader, opts, ownOpts?: {subLayoutFn?: LayoutFn;}){
	//check for simpler cases
	if (node.children.length == 0){
		return oneSqrLayoutFn(node, pos, dims, false, opts);
	} else if (node.children.every(n => n.children.length == 0)){
		return sqrLayoutFn(node, pos, dims, showHeader, opts);
	}
	//consider area excluding header and top/left spacing
	let headerSz = showHeader ? opts.headerSz : 0;
	let newPos = [opts.tileSpacing, opts.tileSpacing + headerSz];
	let newDims = [dims[0] - opts.tileSpacing, dims[1] - opts.tileSpacing - headerSz];
	if (newDims[0] * newDims[1] <= 0){
		return null;
	}
	//try finding arrangement with low empty space
		//done by searching possible row groupings, allocating within rows using dCounts, and trimming empty space
	let numChildren = node.children.length;
	let rowBrks: number[] = []; //will hold indices for nodes at which each row starts
	let lowestEmpSpc = Number.POSITIVE_INFINITY;
	let usedChildLyts = null, usedEmpRight = 0, usedEmpBottom = 0;
	rowBrksLoop:
	while (true){
		//update rowBrks or exit loop
		switch (opts.rectMode){
			case 'horz':
				if (rowBrks.length == 0){
					rowBrks = [0];
				} else {
					break rowBrksLoop;
				}
				break;
			case 'vert':
				if (rowBrks.length == 0){
					rowBrks = range(numChildren);
				} else {
					break rowBrksLoop;
				}
				break;
			case 'linear':
				if (rowBrks.length == 0){
					rowBrks = [0];
				} else if (rowBrks.length == numChildren){
					rowBrks = range(numChildren);
				} else {
					break rowBrksLoop;
				}
				break;
			case 'auto':
				if (rowBrks.length == 0){
					rowBrks = [0];
				} else {
					let updated = updateAscSeq(rowBrks, numChildren);
					if (!updated){
						break rowBrksLoop;
					}
				}
				break;
		}
		//create array-of-arrays representing each rows' cells' dCounts
		let rowsOfCnts: number[][] = new Array(rowBrks.length);
		for (let rowIdx = 0; rowIdx < rowBrks.length; rowIdx++){
			let numNodes = (rowIdx < rowBrks.length - 1) ?
				rowBrks[rowIdx + 1] - rowBrks[rowIdx] :
				numChildren - rowBrks[rowIdx];
			let rowNodeIdxs = range(numNodes).map(i => i + rowBrks![rowIdx]);
			rowsOfCnts[rowIdx] = rowNodeIdxs.map(idx => node.children[idx].dCount);
		}
		//get initial cell dims
		let cellWs: number[][] = new Array(rowsOfCnts.length);
		for (let rowIdx = 0; rowIdx < rowsOfCnts.length; rowIdx++){
			let rowCount = arraySum(rowsOfCnts[rowIdx]);
			cellWs[rowIdx] = range(rowsOfCnts[rowIdx].length).map(
				colIdx => rowsOfCnts[rowIdx][colIdx] / rowCount * newDims[0]);
		}
		let totalDCount = arraySum(node.children.map(n => n.dCount));
		let cellHs = rowsOfCnts.map(rowOfCnts => arraySum(rowOfCnts) / totalDCount * newDims[1]);
		//check min-tile-size, attempting to reallocate space if needed
		for (let rowIdx = 0; rowIdx < rowsOfCnts.length; rowIdx++){
			let newWs = limitVals(cellWs[rowIdx], opts.minTileSz + opts.tileSpacing, Number.POSITIVE_INFINITY);
			if (newWs == null){
				continue rowBrksLoop;
			}
			cellWs[rowIdx] = newWs;
		}
		cellHs = limitVals(cellHs, opts.minTileSz + opts.tileSpacing, Number.POSITIVE_INFINITY)!;
		if (cellHs == null){
			continue rowBrksLoop;
		}
		//get cell xy-coordinates
		let cellXs: number[][] = new Array(rowsOfCnts.length);
		for (let rowIdx = 0; rowIdx < rowBrks.length; rowIdx++){
			cellXs[rowIdx] = [0];
			for (let colIdx = 1; colIdx < rowsOfCnts[rowIdx].length; colIdx++){
				cellXs[rowIdx].push(cellXs[rowIdx][colIdx - 1] + cellWs[rowIdx][colIdx - 1]);
			}
		}
		let cellYs: number[] = new Array(rowsOfCnts.length).fill(0);
		for (let rowIdx = 1; rowIdx < rowBrks.length; rowIdx++){
			cellYs[rowIdx] = cellYs[rowIdx - 1] + cellHs[rowIdx - 1];
		}
		//determine child layouts, resizing cells to reduce empty space
		let childLyts: LayoutNode[] = new Array(numChildren);
		let empRight = Number.POSITIVE_INFINITY, empBottom = 0;
		for (let rowIdx = 0; rowIdx < rowBrks.length; rowIdx++){
			for (let colIdx = 0; colIdx < rowsOfCnts[rowIdx].length; colIdx++){
				let nodeIdx = rowBrks[rowIdx] + colIdx;
				let child = node.children[nodeIdx];
				let childPos: [number, number] = [newPos[0] + cellXs[rowIdx][colIdx], newPos[1] + cellYs[rowIdx]];
				let childDims: [number, number] = [
					cellWs[rowIdx][colIdx] - opts.tileSpacing,
					cellHs[rowIdx] - opts.tileSpacing
				];
				let newChild: LayoutNode | null = null;
				if (child.children.length == 0){
					newChild = oneSqrLayoutFn(child, childPos, childDims, false, opts);
				} else if (child.children.every(n => n.children.length == 0)){
					newChild = sqrLayoutFn(child, childPos, childDims, true, opts);
				} else {
					let layoutFn = (ownOpts && ownOpts.subLayoutFn) || rectLayoutFn;
					newChild = layoutFn(child, childPos, childDims, true, opts);
				}
				if (newChild == null){
					continue rowBrksLoop;
				}
				childLyts[nodeIdx] = newChild;
				//remove horizontal empty space by trimming cell and moving/expanding any next cell
				let horzEmp = childDims[0] - newChild.dims[0];
				cellWs[rowIdx][colIdx] -= horzEmp;
				if (colIdx < rowsOfCnts[rowIdx].length - 1){
					cellXs[rowIdx][colIdx + 1] -= horzEmp;
					cellWs[rowIdx][colIdx + 1] += horzEmp;
				} else {
					empRight = Math.min(empRight, horzEmp);
				}
			}
			//remove vertical empty space by trimming row and moving/expanding any next row
			let childUsedHs = range(rowsOfCnts[rowIdx].length).map(
				colIdx => childLyts[rowBrks[rowIdx] + colIdx].dims[1]);
			let vertEmp = cellHs[rowIdx] - opts.tileSpacing - Math.max(...childUsedHs);
			cellHs[rowIdx] -= vertEmp;
			if (rowIdx < rowBrks.length - 1){
				cellYs[rowIdx + 1] -= vertEmp;
				cellHs[rowIdx + 1] += vertEmp;
			} else {
				empBottom = vertEmp;
			}
		}
		//get empty space
		let usedSpc = arraySum(childLyts.map(l => (l.dims[0] + opts.tileSpacing) * (l.dims[1] + opts.tileSpacing)));
		let empSpc = newDims[0] * newDims[1] - usedSpc;
		//check with best-so-far
		if (empSpc < lowestEmpSpc){
			lowestEmpSpc = empSpc;
			usedChildLyts = childLyts;
			usedEmpRight = empRight;
			usedEmpBottom = empBottom;
		}
	}
	if (usedChildLyts == null){ //hint for tsc
		return null;
	}
	//create layout
	let usedDims: [number,number] = [dims[0] - usedEmpRight, dims[1] - usedEmpBottom];
	let newNode = new LayoutNode(node.tolNode, usedChildLyts, pos, usedDims, {showHeader, empSpc: lowestEmpSpc});
	usedChildLyts.forEach(n => n.parent = newNode);
	return newNode;
}
//lays out nodes by pushing leaves to one side, and using rectLayoutFn() for the non-leaves
	//with layout option 'sweepingToParent', leaves from child nodes may occupy a parent's leaf-section
	//'sepArea' represents a usable leaf-section area from a direct parent, 
		//and is altered to represent the area used, which provides the parent information for reducing empty space
let sweepLayoutFn: LayoutFn = function (node, pos, dims, showHeader, opts, ownOpts?: {sepArea?: SepSweptArea}){
	//separate leaf and non-leaf nodes
	let leaves: LayoutNode[] = [], nonLeaves: LayoutNode[] = [];
	let reverseMap: {isLeaf: boolean, idx: number}[] = []; //used to put separated nodes into old order
	node.children.forEach(child => {
		if (child.children.length == 0){
			leaves.push(child);
			reverseMap.push({isLeaf: true, idx: leaves.length-1});
		} else {
			nonLeaves.push(child);
			reverseMap.push({isLeaf: false, idx: nonLeaves.length-1});
		}
	});
	//check for simpler cases
	if (node.children.length == 0){
		return oneSqrLayoutFn(node, pos, dims, false, opts);
	} else if (nonLeaves.length == 0){
		return sqrLayoutFn(node, pos, dims, showHeader, opts);
	} else if (leaves.length == 0){
		return rectLayoutFn(node, pos, dims, showHeader, opts, {subLayoutFn: sweepLayoutFn});
	}
	//some variables
	let headerSz = showHeader ? opts.headerSz : 0;
	let leavesLyt: LayoutNode | null = null, nonLeavesLyt: LayoutNode | null = null, sweptLeft = false;
	let sepArea: SepSweptArea | null = null, sepAreaUsed = false; //represents leaf-section area provided for a child
	//try using parent-provided area
	let parentArea = (opts.sweepingToParent && ownOpts) ? ownOpts.sepArea : null; //represents area provided by parent
	let usingParentArea = false; 
	if (parentArea != null){
		//attempt leaves layout
		sweptLeft = parentArea.sweptLeft;
		let tempTree = new LayoutNode(new TolNode('SWEEP_' + node.tolNode.name), leaves);
			//not updating child nodes to point to tempTree as a parent seems acceptable here
		leavesLyt = sqrLayoutFn(tempTree, [0,0], parentArea.dims, !sweptLeft, opts);
		if (leavesLyt != null){
			//move leaves to parent area
			leavesLyt.children.map(lyt => {
				lyt.pos[0] += parentArea!.pos[0];
				lyt.pos[1] += parentArea!.pos[1];
			});
			//attempt non-leaves layout
			let newDims: [number,number] = [dims[0], dims[1] - (sweptLeft ? headerSz : 0)];
			tempTree = new LayoutNode(new TolNode('SWEEP_REM_' + node.tolNode.name), nonLeaves);
			let sepAreaLen = 0;
			if (nonLeaves.length > 1){
				nonLeavesLyt = rectLayoutFn(tempTree, [0,0], newDims, false, opts, {subLayoutFn: sweepLayoutFn});
			} else {
				//get leftover area usable by non-leaf child
				if (sweptLeft){
					sepArea = new SepSweptArea(
						[parentArea.pos[0], parentArea.pos[1] + leavesLyt.dims[1] - (opts.tileSpacing + headerSz)],
							//the y-coord subtraction is to make the position relative to a direct non-leaf child
						[parentArea.dims[0], parentArea.dims[1] - leavesLyt.dims[1] - opts.tileSpacing*2],
						sweptLeft
					);
					sepAreaLen = sepArea.dims[1];
				} else {
					sepArea = new SepSweptArea(
						[parentArea.pos[0] + leavesLyt.dims[0] - opts.tileSpacing, parentArea.pos[1] + headerSz],
						[parentArea.dims[0] - leavesLyt.dims[0] - opts.tileSpacing*2, parentArea.dims[1] - headerSz],
						sweptLeft
					);
					sepAreaLen = sepArea.dims[0];
				}
				//attempt layout
				nonLeavesLyt = rectLayoutFn(tempTree, [0,0], newDims, false, opts, {subLayoutFn:
					((n,p,d,h,o) => sweepLayoutFn(n,p,d,h,o,{sepArea:sepArea})) as LayoutFn});
			}
			if (nonLeavesLyt != null){
				usingParentArea = true;
				//adjust child positions
				if (sweptLeft){
					nonLeavesLyt.children.forEach(lyt => {lyt.pos[1] += headerSz});
				}
				//update parentArea to represent space used
				if (sweptLeft){
					parentArea.dims[1] = leavesLyt.dims[1];
					if (sepArea != null && sepAreaLen > sepArea.dims[1]){ //if space used by child
						parentArea.dims[1] += sepArea.dims[1] + opts.tileSpacing*2;
					}
				} else {
					parentArea.dims[0] = leavesLyt.dims[0];
					if (sepArea != null && sepAreaLen > sepArea.dims[0]){
						parentArea.dims[0] += sepArea.dims[0] + opts.tileSpacing*2;
					}
				}
				//align parentArea size with non-leaves area
				if (sweptLeft){
					if (parentArea.pos[1] + parentArea.dims[1] > nonLeavesLyt.dims[1] + headerSz){
						nonLeavesLyt.dims[1] = parentArea.pos[1] + parentArea.dims[1] - headerSz;
					} else {
						parentArea.dims[1] = nonLeavesLyt.dims[1] + headerSz - parentArea.pos[1];
					}
				} else {
					if (parentArea.pos[0] + parentArea.dims[0] > nonLeavesLyt.dims[0]){
						nonLeavesLyt.dims[0] = parentArea.pos[0] + parentArea.dims[0];
					} else {
						parentArea.dims[0] = nonLeavesLyt.dims[0] - parentArea.pos[0];
					}
				}
				//adjust area to avoid overlap with non-leaves
				if (sweptLeft){
					parentArea.dims[0] -= opts.tileSpacing;
				} else {
					parentArea.dims[1] -= opts.tileSpacing;
				}
			}
		}
	}
	//try using own area
	if (!usingParentArea){
		//choose proportion of area to use for leaves
		let ratio: number; //area-for-leaves / area-for-non-leaves
		let nonLeavesTiles = arraySum(nonLeaves.map(n => n.dCount));
		switch (opts.sweptNodesPrio){
			case 'linear': 
				ratio = leaves.length / (leaves.length + nonLeavesTiles);
				break;
			case 'sqrt':
				ratio = Math.sqrt(leaves.length) / (Math.sqrt(leaves.length) + Math.sqrt(nonLeavesTiles));
				break;
			case 'pow-2/3':
				ratio = Math.pow(leaves.length, 2/3) /
					(Math.pow(leaves.length, 2/3) + Math.pow(nonLeavesTiles, 2/3));
				break;
		}
		//attempt leaves layout
		let newPos = [0, headerSz];
		let newDims: [number,number] = [dims[0], dims[1] - headerSz];
		let tempTree = new LayoutNode(new TolNode('SWEEP_' + node.tolNode.name), leaves);
		let minSz = opts.minTileSz + opts.tileSpacing*2;
		let sweptW = Math.max(minSz, newDims[0] * ratio), sweptH = Math.max(minSz, newDims[1] * ratio);
		switch (opts.sweepMode){
			case 'left':
				leavesLyt = sqrLayoutFn(tempTree, [0,0], [sweptW, newDims[1]], false, opts);
				sweptLeft = true;
				break;
			case 'top':
				leavesLyt = sqrLayoutFn(tempTree, [0,0], [newDims[0], sweptH], false, opts);
				sweptLeft = false;
				break;
			case 'shorter':
				let documentAR = document.documentElement.clientWidth / document.documentElement.clientHeight;
				if (documentAR >= 1){
					leavesLyt = sqrLayoutFn(tempTree, [0,0], [sweptW, newDims[1]], false, opts);
					sweptLeft = true;
				} else {
					leavesLyt = sqrLayoutFn(tempTree, [0,0], [newDims[0], sweptH], false, opts);
					sweptLeft = false;
				}
				break;
			case 'auto':
				let leftLayout = sqrLayoutFn(tempTree, [0,0], [sweptW, newDims[1]], false, opts);
				let topLayout = sqrLayoutFn(tempTree, [0,0], [newDims[0], sweptH], false, opts);
				if (leftLayout != null && topLayout != null){
					leavesLyt = (leftLayout.empSpc < topLayout.empSpc) ? leftLayout : topLayout;
				} else {
					leavesLyt = leftLayout || topLayout;
				}
				sweptLeft = (leavesLyt == leftLayout);
				break;
		}
		if (leavesLyt == null){
			return null;
		}
		leavesLyt.children.forEach(lyt => {lyt.pos[1] += headerSz});
		//attempt non-leaves layout
		if (sweptLeft){
			newPos[0] += leavesLyt.dims[0] - opts.tileSpacing;
			newDims[0] += -leavesLyt.dims[0] + opts.tileSpacing;
		} else {
			newPos[1] += leavesLyt.dims[1] - opts.tileSpacing;
			newDims[1] += -leavesLyt.dims[1] + opts.tileSpacing
		}
		tempTree = new LayoutNode(new TolNode('SWEEP_REM_' + node.tolNode.name), nonLeaves);
		if (nonLeaves.length > 1){
			nonLeavesLyt = rectLayoutFn(tempTree, [0,0], newDims, false, opts, {subLayoutFn: sweepLayoutFn});
		} else {
			//get leftover area usable by non-leaf child
			let sepAreaLen;
			if (sweptLeft){
				sepAreaLen = newDims[1] - leavesLyt.dims[1] - opts.tileSpacing;
				sepArea = new SepSweptArea( //position relative to a non-leaf child
					[-leavesLyt.dims[0] + opts.tileSpacing, leavesLyt.dims[1] - opts.tileSpacing],
					[leavesLyt.dims[0], sepAreaLen],
					sweptLeft
				);
			} else {
				sepAreaLen = newDims[0] - leavesLyt.dims[0] - opts.tileSpacing;
				sepArea = new SepSweptArea(
					[leavesLyt.dims[0] - opts.tileSpacing, -leavesLyt.dims[1] + opts.tileSpacing],
					[sepAreaLen, leavesLyt.dims[1]],
					sweptLeft
				);
			}
			//attempt layout
			nonLeavesLyt = rectLayoutFn(tempTree, [0,0], newDims, false, opts, {subLayoutFn:
				((n,p,d,h,o) => sweepLayoutFn(n,p,d,h,o,{sepArea:sepArea})) as LayoutFn});
			if ((sweptLeft && sepAreaLen > sepArea.dims[1]) || (!sweptLeft && sepAreaLen > sepArea.dims[0])){
				sepAreaUsed = true;
			}
		}
		if (nonLeavesLyt == null){
			return null;
		}
		nonLeavesLyt.children.forEach(lyt => {
			lyt.pos[0] += newPos[0];
			lyt.pos[1] += newPos[1];
		});
	}
	//return combined layouts
	if (leavesLyt == null || nonLeavesLyt == null){ //hint for tsc
		return null;
	}
	let layoutsInOldOrder = reverseMap.map(({isLeaf, idx}) => (isLeaf ? leavesLyt : nonLeavesLyt)!.children[idx]);
	let usedDims: [number, number];
	if (usingParentArea){
		usedDims = [nonLeavesLyt.dims[0], nonLeavesLyt.dims[1] + (sweptLeft ? headerSz : 0)];
	} else {
		if (sweptLeft){
			usedDims = [
				leavesLyt.dims[0] + nonLeavesLyt.dims[0] - opts.tileSpacing,
				Math.max(leavesLyt.dims[1] + (sepAreaUsed ? sepArea!.dims[1] : 0), nonLeavesLyt.dims[1]) + headerSz
			];
		} else {
			usedDims = [
				Math.max(leavesLyt.dims[0] + (sepAreaUsed ? sepArea!.dims[0] : 0), nonLeavesLyt.dims[0]),
				leavesLyt.dims[1] + nonLeavesLyt.dims[1] - opts.tileSpacing + headerSz
			];
		}
	}
	let empSpc = (!usingParentArea ? leavesLyt.empSpc : 0) + nonLeavesLyt.empSpc;
	let newNode = new LayoutNode(node.tolNode, layoutsInOldOrder, pos, usedDims,
		{showHeader, empSpc, sepSweptArea: usingParentArea ? parentArea! : null});
	layoutsInOldOrder.forEach(n => n.parent = newNode);
	return newNode;
}

//returns [0, ..., len]
function range(len: number){
	return [...Array(len).keys()];
}
//returns sum of array values
function arraySum(array: number[]){
	return array.reduce((x,y) => x+y);
}
//returns array copy with vals clipped to within [min,max], redistributing to compensate (returns null on failure)
function limitVals(arr: number[], min: number, max: number){
	let vals = [...arr];
	let clipped = new Array(vals.length).fill(false);
	let owedChg = 0; //stores total change made after clipping values
	while (true){
		//clip values
		for (let i = 0; i < vals.length; i++){
			if (clipped[i]){
				continue;
			}
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
		if (Math.abs(owedChg) < Number.EPSILON){
			return vals;
		}
		//compensate for changes made
		let indicesToUpdate = (owedChg > 0) ?
			range(vals.length).filter(idx => vals[idx] < max) :
			range(vals.length).filter(idx => vals[idx] > min);
		if (indicesToUpdate.length == 0){
			return null;
		}
		for (let i of indicesToUpdate){
			vals[i] += owedChg / indicesToUpdate.length;
		}
		owedChg = 0;
	}
}
//usable to iterate through possible int arrays with ascending values in the range 0 to maxLen-1, starting with [0]
	//eg: with maxLen 3, updates [0] to [0,1], then to [0,2], then [0,1,2], then null
function updateAscSeq(seq: number[], maxLen: number){
	//try increasing last element, then preceding elements, then extending the array
	let i = seq.length - 1;
	while (true){
		if (i > 0 && seq[i] < (maxLen - 1) - (seq.length - 1 - i)){
			seq[i]++;
			return true;
		} else if (i > 0){
			i--;
		} else {
			if (seq.length < maxLen){
				seq.push(0);
				seq.splice(0, seq.length, ...range(seq.length));
				return true;
			} else {
				return false;
			}
		}
	}
}
