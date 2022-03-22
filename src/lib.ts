/*
 * Contains classes used for representing tree-of-life data, and tile-based layouts of such data.
 *
 * Generally, given a TolNode with child TolNodes representing tree-of-life T,
 * initLayoutTree() produces a tree structure representing a subtree of T,
 * which is passed to tryLayout(), which alters data fields to represent a tile-based layout.
 * The tree structure consists of LayoutNode objects, each of which holds placement info for a linked TolNode.
 */

// Represents a tree-of-life node/tree
export class TolNode {
	name: string;
	children: TolNode[];
	constructor(name: string, children: TolNode[] = []){
		this.name = name;
		this.children = children;
	}
}
// Represents a node/tree, and holds layout data for a TolNode node/tree
export class LayoutNode {
	tolNode: TolNode;
	children: LayoutNode[];
	parent: LayoutNode | null;
	// Used for rendering a corresponding tile
	pos: [number, number];
	dims: [number, number];
	showHeader: boolean;
	sepSweptArea: SepSweptArea | null;
	hidden: boolean;
	// Used for layout heuristics and info display
	dCount: number; // Number of descendant leaf nodes
	depth: number; // Number of ancestor nodes
	empSpc: number; // Amount of unused space (in pixels)
	// Creates object with given fields ('parent' are 'depth' are generally initialised later, 'dCount' is computed)
	constructor(tolNode: TolNode, children: LayoutNode[]){
		this.tolNode = tolNode;
		this.children = children;
		this.parent = null;
		this.pos = [0,0];
		this.dims = [0,0];
		this.showHeader = false;
		this.sepSweptArea = null;
		this.hidden = false;
		this.dCount = children.length == 0 ? 1 : arraySum(children.map(n => n.dCount));
		this.depth = 0;
		this.empSpc = 0;
	}
	// Creates new node tree with the same structure (fields like 'pos' are set to defaults)
	// 'chg' is usable to apply a change to the resultant tree
	cloneNodeTree(chg?: LayoutTreeChg){
		let newNode: LayoutNode;
		if (chg != null && this == chg.node){
			switch (chg.type){
				case 'expand':
					let children = this.tolNode.children.map((n: TolNode) => new LayoutNode(n, []));
					newNode = new LayoutNode(this.tolNode, children);
					newNode.children.forEach(n => {
						n.parent = newNode;
						n.depth = this.depth + 1;
					});
					break;
				case 'collapse':
					newNode = new LayoutNode(this.tolNode, []);
					break;
			}
		} else {
			let children = this.children.map(n => n.cloneNodeTree(chg));
			newNode = new LayoutNode(this.tolNode, children);
			children.forEach(n => {n.parent = newNode});
		}
		newNode.depth = this.depth;
		return newNode;
	}
	// Copies render-relevant data to a given LayoutNode tree
	// If a target node has more/less children, removes/gives own children
	copyTreeForRender(target: LayoutNode): void {
		target.pos = this.pos;
		target.dims = this.dims;
		target.showHeader = this.showHeader;
		target.sepSweptArea = this.sepSweptArea;
		target.dCount = this.dCount; // Copied for structural-consistency
		target.empSpc = this.empSpc; // Currently redundant, but maintains data-consistency
		// Handle children
		if (this.children.length == target.children.length){
			this.children.forEach((n,i) => n.copyTreeForRender(target.children[i]));
		} else if (this.children.length < target.children.length){
			target.children = [];
		} else {
			target.children = this.children;
			target.children.forEach(n => {n.parent = target});
		}
	}
	// Assigns render-relevant data to this single node
	assignLayoutData(pos=[0,0] as [number,number], dims=[0,0] as [number,number],
		{showHeader=false, sepSweptArea=null as SepSweptArea|null, empSpc=0} = {}){
		this.pos = [...pos];
		this.dims = [...dims];
		this.showHeader = showHeader;
		this.sepSweptArea = sepSweptArea;
		this.empSpc = empSpc;
	}
	// Used to update a LayoutNode tree's dCount fields after adding/removing a node's children
	static updateDCounts(node: LayoutNode | null, diff: number): void {
		while (node != null){
			node.dCount += diff;
			node = node.parent;
		}
	}
	//
	static hideUpward(node: LayoutNode){
		if (node.parent != null){
			node.parent.hidden = true;
			node.parent.children.filter(n => n != node).forEach(n => LayoutNode.hideDownward(n));
			LayoutNode.hideUpward(node.parent);
		}
	}
	static hideDownward(node: LayoutNode){
		node.hidden = true;
		node.children.forEach(n => {
			LayoutNode.hideDownward(n)
		});
	}
}
// Contains settings that affect how layout is done
export type LayoutOptions = {
	tileSpacing: number; // Spacing between tiles, in pixels (ignoring borders)
	headerSz: number;
	minTileSz: number; // Minimum size of a tile edge, in pixels (ignoring borders)
	maxTileSz: number;
	layoutType: 'sqr' | 'rect' | 'sweep'; // The LayoutFn function to use
	rectMode: 'horz' | 'vert' | 'linear' | 'auto'; // Layout in 1 row, 1 column, 1 row or column, or multiple rows
	sweepMode: 'left' | 'top' | 'shorter' | 'auto'; // Sweep to left, top, shorter-side, or to minimise empty space
	sweptNodesPrio: 'linear' | 'sqrt' | 'pow-2/3'; // Specifies allocation of space to swept-vs-remaining nodes
	sweepingToParent: boolean; // Allow swept nodes to occupy empty space in a parent's swept-leaves area
};
export type LayoutTreeChg = {
	type: 'expand' | 'collapse';
	node: LayoutNode;
}
// Used with layout option 'sweepingToParent', and represents, for a LayoutNode, a parent area to place leaf nodes in
export class SepSweptArea {
	pos: [number, number];
	dims: [number, number];
	sweptLeft: boolean; // True if the parent's leaves were swept left
	constructor(pos: [number, number], dims: [number, number], sweptLeft: boolean){
		this.pos = pos;
		this.dims = dims;
		this.sweptLeft = sweptLeft;
	}
	clone(): SepSweptArea {
		return new SepSweptArea([...this.pos], [...this.dims], this.sweptLeft);
	}
}

// Creates a LayoutNode representing a TolNode tree, up to a given depth (0 means just the root)
export function initLayoutTree(tol: TolNode, depth: number): LayoutNode {
	function initHelper(tolNode: TolNode, depthLeft: number, atDepth: number = 0): LayoutNode {
		if (depthLeft == 0){
			let node = new LayoutNode(tolNode, []);
			node.depth = atDepth;
			return node;
		} else {
			let children = tolNode.children.map((n: TolNode) => initHelper(n, depthLeft-1, atDepth+1));
			let node = new LayoutNode(tolNode, children);
			children.forEach(n => n.parent = node);
			return node;
		}
	}
	return initHelper(tol, depth);
}
// Attempts layout on a LayoutNode's corresponding TolNode tree, for an area with given xy-position and width+height
// 'allowCollapse' allows the layout algorithm to collapse nodes to avoid layout failure
// 'chg' allows for performing layout after expanding/collapsing a node
export function tryLayout(layoutTree: LayoutNode, pos: [number,number], dims: [number,number],
	options: LayoutOptions, allowCollapse: boolean = false, chg?: LayoutTreeChg){
	// Create a new LayoutNode tree, in case of layout failure
	let tempTree = layoutTree.cloneNodeTree(chg);
	let success: boolean;
	switch (options.layoutType){
		case 'sqr':   success =   sqrLayout(tempTree, pos, dims, true, allowCollapse, options); break;
		case 'rect':  success =  rectLayout(tempTree, pos, dims, true, allowCollapse, options); break;
		case 'sweep': success = sweepLayout(tempTree, pos, dims, true, allowCollapse, options); break;
	}
	if (success){
		// Center in layout area
		tempTree.pos[0] += (dims[0] - tempTree.dims[0]) / 2;
		tempTree.pos[1] += (dims[1] - tempTree.dims[1]) / 2;
		// Apply to active LayoutNode tree
		tempTree.copyTreeForRender(layoutTree);
	}
	return success;
}

// Type for functions called by tryLayout() to perform layout
// Given a LayoutNode tree, determines and records a new layout by setting fields of nodes in the tree
// Returns a boolean indicating success
type LayoutFn = (
	node: LayoutNode,
	pos: [number, number],
	dims: [number, number],
	showHeader: boolean,
	allowCollapse: boolean,
	opts: LayoutOptions,
	ownOpts?: any,
) => boolean;
// Lays out node as one square, ignoring child nodes (used for base cases)
let oneSqrLayout: LayoutFn = function (node, pos, dims, showHeader, allowCollapse, opts){
	let tileSz = Math.min(dims[0], dims[1], opts.maxTileSz);
	if (tileSz < opts.minTileSz){
		return false;
	}
	node.assignLayoutData(pos, [tileSz,tileSz], {showHeader, empSpc: dims[0]*dims[1] - tileSz**2});
	return true;
}
// Lays out nodes as squares within a grid with intervening+surrounding spacing
let sqrLayout: LayoutFn = function (node, pos, dims, showHeader, allowCollapse, opts){
	if (node.children.length == 0){
		return oneSqrLayout(node, pos, dims, false, false, opts);
	}
	// Consider area excluding header and top/left spacing
	let headerSz = showHeader ? opts.headerSz : 0;
	let newPos = [opts.tileSpacing, opts.tileSpacing + headerSz];
	let newDims = [dims[0] - opts.tileSpacing, dims[1] - opts.tileSpacing - headerSz];
	if (newDims[0] * newDims[1] <= 0){
		return false;
	}
	// Find number of rows/columns with least empty space
	let numChildren = node.children.length;
	let areaAR = newDims[0] / newDims[1]; // Aspect ratio
	let lowestEmpSpc = Number.POSITIVE_INFINITY, usedNumCols = 0, usedNumRows = 0, usedTileSz = 0;
	for (let numCols = 1; numCols <= numChildren; numCols++){
		let numRows = Math.ceil(numChildren / numCols);
		let gridAR = numCols / numRows;
		let usedFrac = // Fraction of area occupied by maximally-fitting grid
			areaAR > gridAR ? gridAR / areaAR : areaAR / gridAR;
		// Get tile edge length
		let tileSz = (areaAR > gridAR ? newDims[1] / numRows : newDims[0] / numCols) - opts.tileSpacing;
		if (tileSz < opts.minTileSz){
			continue;
		} else if (tileSz > opts.maxTileSz){
			tileSz = opts.maxTileSz;
		}
		// Get empty space
		let empSpc = (1 - usedFrac) * (newDims[0] * newDims[1]) + // Area outside grid plus ...
			(numCols * numRows - numChildren) * (tileSz - opts.tileSpacing)**2; // empty cells within grid
		// Compare with best-so-far
		if (empSpc < lowestEmpSpc){
			lowestEmpSpc = empSpc;
			usedNumCols = numCols;
			usedNumRows = numRows;
			usedTileSz = tileSz;
		}
	}
	if (lowestEmpSpc == Number.POSITIVE_INFINITY){
		if (allowCollapse){
			node.children = [];
			LayoutNode.updateDCounts(node, 1 - node.dCount);
			return oneSqrLayout(node, pos, dims, false, false, opts);
		}
		return false;
	}
	// Layout children
	for (let i = 0; i < numChildren; i++){
		let child = node.children[i];
		let childX = newPos[0] + (i % usedNumCols) * (usedTileSz + opts.tileSpacing);
		let childY = newPos[1] + Math.floor(i / usedNumCols) * (usedTileSz + opts.tileSpacing);
		let success: boolean;
		if (child.children.length == 0){
			success = oneSqrLayout(child, [childX,childY], [usedTileSz,usedTileSz], false, false, opts);
		} else {
			success = sqrLayout(child, [childX,childY], [usedTileSz,usedTileSz], true, allowCollapse, opts);
		}
		if (!success){
			if (allowCollapse){
				node.children = [];
				LayoutNode.updateDCounts(node, 1 - node.dCount);
				return oneSqrLayout(node, pos, dims, false, false, opts);
			}
			return false;
		}
	}
	// Create layout
	let usedDims: [number, number] = [
		usedNumCols * (usedTileSz + opts.tileSpacing) + opts.tileSpacing,
		usedNumRows * (usedTileSz + opts.tileSpacing) + opts.tileSpacing + headerSz,
	];
	let empSpc = // Empty space within usedDims area
		(usedNumCols * usedNumRows - numChildren) * (usedTileSz - opts.tileSpacing)**2 +
		arraySum(node.children.map(child => child.empSpc));
	node.assignLayoutData(pos, usedDims, {showHeader, empSpc});
	return true;
}
// Lays out nodes as rows of rectangles, deferring to sqrLayout() or oneSqrLayout() for simpler cases
//'subLayoutFn' allows other LayoutFns to use this layout, but transfer control back to themselves on recursion
let rectLayout: LayoutFn = function (node, pos, dims, showHeader, allowCollapse, opts,
	ownOpts?: {subLayoutFn?: LayoutFn}){
	// Check for simpler cases
	if (node.children.length == 0){
		return oneSqrLayout(node, pos, dims, false, false, opts);
	} else if (node.children.every(n => n.children.length == 0)){
		return sqrLayout(node, pos, dims, showHeader, allowCollapse, opts);
	}
	// Consider area excluding header and top/left spacing
	let headerSz = showHeader ? opts.headerSz : 0;
	let newPos = [opts.tileSpacing, opts.tileSpacing + headerSz];
	let newDims = [dims[0] - opts.tileSpacing, dims[1] - opts.tileSpacing - headerSz];
	if (newDims[0] * newDims[1] <= 0){
		return false;
	}
	// Try finding arrangement with low empty space
	// Done by searching possible row groupings, allocating within rows using dCounts, and trimming empty space
	let numChildren = node.children.length;
	let rowBrks: number[] = []; // Will hold indices for nodes at which each row starts
	let lowestEmpSpc = Number.POSITIVE_INFINITY;
	let usedTree: LayoutNode | null = null, usedEmpRight = 0, usedEmpBottom = 0;
	const minCellDims = [ // Can situationally assume non-leaf children
		opts.minTileSz + opts.tileSpacing +
			(opts.layoutType == 'sweep' ? opts.tileSpacing*2 : 0),
		opts.minTileSz + opts.tileSpacing +
			(opts.layoutType == 'sweep' ? opts.tileSpacing*2 + opts.headerSz : 0)
	];
	rowBrksLoop:
	while (true){
		// Update rowBrks or exit loop
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
		// Create array-of-arrays representing each rows' cells' dCounts
		let rowsOfCnts: number[][] = new Array(rowBrks.length);
		for (let rowIdx = 0; rowIdx < rowBrks.length; rowIdx++){
			let numNodes = (rowIdx < rowBrks.length - 1) ?
				rowBrks[rowIdx + 1] - rowBrks[rowIdx] :
				numChildren - rowBrks[rowIdx];
			let rowNodeIdxs = range(numNodes).map(i => i + rowBrks![rowIdx]);
			rowsOfCnts[rowIdx] = rowNodeIdxs.map(idx => node.children[idx].dCount);
		}
		// Get initial cell dims
		let cellWs: number[][] = new Array(rowsOfCnts.length);
		for (let rowIdx = 0; rowIdx < rowsOfCnts.length; rowIdx++){
			let rowCount = arraySum(rowsOfCnts[rowIdx]);
			cellWs[rowIdx] = range(rowsOfCnts[rowIdx].length).map(
				colIdx => rowsOfCnts[rowIdx][colIdx] / rowCount * newDims[0]);
		}
		let totalDCount = arraySum(node.children.map(n => n.dCount));
		let cellHs = rowsOfCnts.map(rowOfCnts => arraySum(rowOfCnts) / totalDCount * newDims[1]);
		// Check min-tile-size, attempting to reallocate space if needed
		for (let rowIdx = 0; rowIdx < rowsOfCnts.length; rowIdx++){
			let newWs = limitVals(cellWs[rowIdx], minCellDims[0], Number.POSITIVE_INFINITY);
			if (newWs == null){
				continue rowBrksLoop;
			}
			cellWs[rowIdx] = newWs;
		}
		cellHs = limitVals(cellHs, minCellDims[1], Number.POSITIVE_INFINITY)!;
		if (cellHs == null){
			continue rowBrksLoop;
		}
		// Get cell xy-coordinates
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
		// Determine child layouts, resizing cells to reduce empty space
		let tempTree: LayoutNode = node.cloneNodeTree();
		let empRight = Number.POSITIVE_INFINITY, empBottom = 0;
		for (let rowIdx = 0; rowIdx < rowBrks.length; rowIdx++){
			for (let colIdx = 0; colIdx < rowsOfCnts[rowIdx].length; colIdx++){
				let nodeIdx = rowBrks[rowIdx] + colIdx;
				let child: LayoutNode = tempTree.children[nodeIdx];
				let childPos: [number, number] = [newPos[0] + cellXs[rowIdx][colIdx], newPos[1] + cellYs[rowIdx]];
				let childDims: [number, number] = [
					cellWs[rowIdx][colIdx] - opts.tileSpacing,
					cellHs[rowIdx] - opts.tileSpacing
				];
				let success: boolean;
				if (child.children.length == 0){
					success = oneSqrLayout(child, childPos, childDims, false, false, opts);
				} else if (child.children.every(n => n.children.length == 0)){
					success = sqrLayout(child, childPos, childDims, true, allowCollapse, opts);
				}  else {
					let layoutFn = (ownOpts && ownOpts.subLayoutFn) || rectLayout;
					success = layoutFn(child, childPos, childDims, true, allowCollapse, opts);
				}
				if (!success){
					continue rowBrksLoop;
				}
				// Remove horizontal empty space by trimming cell and moving/expanding any next cell
				let horzEmp = childDims[0] - child.dims[0];
				cellWs[rowIdx][colIdx] -= horzEmp;
				if (colIdx < rowsOfCnts[rowIdx].length - 1){
					cellXs[rowIdx][colIdx + 1] -= horzEmp;
					cellWs[rowIdx][colIdx + 1] += horzEmp;
				} else {
					empRight = Math.min(empRight, horzEmp);
				}
			}
			// Remove vertical empty space by trimming row and moving/expanding any next row
			let childUsedHs = range(rowsOfCnts[rowIdx].length).map(
				colIdx => tempTree.children[rowBrks[rowIdx] + colIdx].dims[1]);
			let vertEmp = cellHs[rowIdx] - opts.tileSpacing - Math.max(...childUsedHs);
			cellHs[rowIdx] -= vertEmp;
			if (rowIdx < rowBrks.length - 1){
				cellYs[rowIdx + 1] -= vertEmp;
				cellHs[rowIdx + 1] += vertEmp;
			} else {
				empBottom = vertEmp;
			}
		}
		// Get empty space
		let usedSpc = arraySum(tempTree.children.map(
			child => (child.dims[0] + opts.tileSpacing) * (child.dims[1] + opts.tileSpacing) - child.empSpc));
		let empSpc = newDims[0] * newDims[1] - usedSpc;
		// Check with best-so-far
		if (empSpc < lowestEmpSpc){
			lowestEmpSpc = empSpc;
			usedTree = tempTree;
			usedEmpRight = empRight;
			usedEmpBottom = empBottom;
		}
	}
	if (usedTree == null){ // If no found layout
		if (allowCollapse){
			node.children = [];
			LayoutNode.updateDCounts(node, 1 - node.dCount);
			return oneSqrLayout(node, pos, dims, false, false, opts);
		}
		return false;
	}
	// Create layout
	usedTree.copyTreeForRender(node);
	let usedDims: [number, number] = [dims[0] - usedEmpRight, dims[1] - usedEmpBottom];
	node.assignLayoutData(pos, usedDims, {showHeader, empSpc: lowestEmpSpc});
	return true;
}
// Lays out nodes by pushing leaves to one side, and using rectLayout() for the non-leaves
// With layout option 'sweepingToParent', leaves from child nodes may occupy a parent's leaf-section
//'sepArea' represents a usable leaf-section area from a direct parent,
	//and is altered to represent the area used, which the parent can use for reducing empty space
let sweepLayout: LayoutFn = function (node, pos, dims, showHeader, allowCollapse, opts,
	ownOpts?: {sepArea?: SepSweptArea}){
	// Separate leaf and non-leaf nodes
	let leaves: LayoutNode[] = [], nonLeaves: LayoutNode[] = [];
	node.children.forEach(child => (child.children.length == 0 ? leaves : nonLeaves).push(child));
	// Check for simpler cases
	if (node.children.length == 0){
		return oneSqrLayout(node, pos, dims, false, false, opts);
	} else if (nonLeaves.length == 0){
		return sqrLayout(node, pos, dims, showHeader, allowCollapse, opts);
	} else if (leaves.length == 0){
		return rectLayout(node, pos, dims, showHeader, allowCollapse, opts, {subLayoutFn: sweepLayout});
	}
	// Some variables
	let headerSz = showHeader ? opts.headerSz : 0;
	let leavesLyt: LayoutNode | null = null, nonLeavesLyt: LayoutNode | null = null, sweptLeft = false;
	let sepArea: SepSweptArea | null = null, sepAreaUsed = false; // Represents leaf-section area provided for a child
	// Try using parent-provided area
	let parentArea = (opts.sweepingToParent && ownOpts) ? ownOpts.sepArea : null; // Represents area provided by parent
	let usingParentArea = false;
	if (parentArea != null){
		// Attempt leaves layout
		sweptLeft = parentArea.sweptLeft;
		leavesLyt = new LayoutNode(new TolNode('SWEEP_' + node.tolNode.name), leaves);
			// Not updating child nodes to point to tempTree as a parent seems acceptable here
		let leavesSuccess = sqrLayout(leavesLyt, [0,0], parentArea.dims, !sweptLeft, false, opts);
		if (leavesSuccess){
			// Move leaves to parent area
			leavesLyt.children.map(lyt => {
				lyt.pos[0] += parentArea!.pos[0];
				lyt.pos[1] += parentArea!.pos[1];
			});
			// Attempt non-leaves layout
			let newDims: [number,number] = [dims[0], dims[1] - (sweptLeft ? headerSz : 0)];
			nonLeavesLyt = new LayoutNode(new TolNode('SWEEP_REM_' + node.tolNode.name), nonLeaves);
			let tempTree: LayoutNode = nonLeavesLyt.cloneNodeTree();
			let sepAreaLen = 0;
			let nonLeavesSuccess: boolean;
			if (nonLeaves.length > 1){
				nonLeavesSuccess = rectLayout(tempTree, [0,0], newDims, false, false, opts, {subLayoutFn:
					((n,p,d,h,a,o) => sweepLayout(n,p,d,h,allowCollapse,o,{sepArea:sepArea})) as LayoutFn});
			} else {
				// Get leftover area usable by non-leaf child
				if (sweptLeft){
					sepArea = new SepSweptArea(
						[parentArea.pos[0], parentArea.pos[1] + leavesLyt.dims[1] - (opts.tileSpacing + headerSz)],
							// The y-coord subtraction is to make the position relative to a direct non-leaf child
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
				// Attempt layout
				nonLeavesSuccess = rectLayout(tempTree, [0,0], newDims, false, false, opts, {subLayoutFn:
					((n,p,d,h,a,o) => sweepLayout(n,p,d,h,allowCollapse,o,{sepArea:sepArea})) as LayoutFn});
			}
			if (nonLeavesSuccess){
				usingParentArea = true;
				tempTree.copyTreeForRender(nonLeavesLyt);
				// Adjust child positions
				if (sweptLeft){
					nonLeavesLyt.children.forEach(lyt => {lyt.pos[1] += headerSz});
				}
				// Update parentArea to represent space used
				if (sweptLeft){
					parentArea.dims[1] = leavesLyt.dims[1];
					if (sepArea != null && sepAreaLen > sepArea.dims[1]){ // If space used by child
						parentArea.dims[1] += sepArea.dims[1] + opts.tileSpacing;
					}
				} else {
					parentArea.dims[0] = leavesLyt.dims[0];
					if (sepArea != null && sepAreaLen > sepArea.dims[0]){
						parentArea.dims[0] += sepArea.dims[0] + opts.tileSpacing;
					}
				}
				// Align parentArea size with non-leaves area
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
				// Adjust area to avoid overlap with non-leaves
				if (sweptLeft){
					parentArea.dims[0] -= opts.tileSpacing;
				} else {
					parentArea.dims[1] -= opts.tileSpacing;
				}
			}
		}
	}
	// Try using own area
	if (!usingParentArea){
		// Choose proportion of area to use for leaves
		let ratio: number; // area-for-leaves / area-for-non-leaves
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
		// Attempt leaves layout
		let newPos = [0, headerSz];
		let newDims: [number,number] = [dims[0], dims[1] - headerSz];
		leavesLyt = new LayoutNode(new TolNode('SWEEP_' + node.tolNode.name), leaves);
		let minSz = opts.minTileSz + opts.tileSpacing*2;
		let sweptW = Math.max(minSz, newDims[0] * ratio), sweptH = Math.max(minSz, newDims[1] * ratio);
		let leavesSuccess: boolean;
		switch (opts.sweepMode){
			case 'left':
				leavesSuccess = sqrLayout(leavesLyt, [0,0], [sweptW, newDims[1]], false, false, opts);
				sweptLeft = true;
				break;
			case 'top':
				leavesSuccess = sqrLayout(leavesLyt, [0,0], [newDims[0], sweptH], false, false, opts);
				sweptLeft = false;
				break;
			case 'shorter':
				let documentAR = document.documentElement.clientWidth / document.documentElement.clientHeight;
				if (documentAR >= 1){
					leavesSuccess = sqrLayout(leavesLyt, [0,0], [sweptW, newDims[1]], false, false, opts);
					sweptLeft = true;
				} else {
					leavesSuccess = sqrLayout(leavesLyt, [0,0], [newDims[0], sweptH], false, false, opts);
					sweptLeft = false;
				}
				break;
			case 'auto':
				// Attempt left-sweep, then top-sweep on a copy, and copy over if better
				leavesSuccess = sqrLayout(leavesLyt, [0,0], [sweptW, newDims[1]], false, false, opts);
				sweptLeft = true;
				let tempTree = leavesLyt.cloneNodeTree();
				let sweptTopSuccess = sqrLayout(tempTree, [0,0], [newDims[0], sweptH], false, false, opts);;
				if (sweptTopSuccess && (!leavesSuccess || tempTree.empSpc < leavesLyt.empSpc)){
					tempTree.copyTreeForRender(leavesLyt);
					sweptLeft = false;
					leavesSuccess = true;
				}
				break;
		}
		if (!leavesSuccess){
			if (allowCollapse){
				node.children = [];
				LayoutNode.updateDCounts(node, 1 - node.dCount);
				return oneSqrLayout(node, pos, dims, false, false, opts);
			}
			return false;
		}
		leavesLyt.children.forEach(lyt => {lyt.pos[1] += headerSz});
		// Attempt non-leaves layout
		if (sweptLeft){
			newPos[0] += leavesLyt.dims[0] - opts.tileSpacing;
			newDims[0] += -leavesLyt.dims[0] + opts.tileSpacing;
		} else {
			newPos[1] += leavesLyt.dims[1] - opts.tileSpacing;
			newDims[1] += -leavesLyt.dims[1] + opts.tileSpacing
		}
		nonLeavesLyt = new LayoutNode(new TolNode('SWEEP_REM_' + node.tolNode.name), nonLeaves);
		let nonLeavesSuccess: boolean;
		if (nonLeaves.length > 1){
			nonLeavesSuccess = rectLayout(nonLeavesLyt, [0,0], newDims, false, false, opts, {subLayoutFn:
				((n,p,d,h,a,o) => sweepLayout(n,p,d,h,allowCollapse,o,{sepArea:sepArea})) as LayoutFn});
		} else {
			// Get leftover area usable by non-leaf child
			let sepAreaLen;
			if (sweptLeft){
				sepAreaLen = newDims[1] - leavesLyt.dims[1] - opts.tileSpacing;
				sepArea = new SepSweptArea(
					[-leavesLyt.dims[0] + opts.tileSpacing, leavesLyt.dims[1] - opts.tileSpacing], //Relative to child
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
			// Attempt layout
			nonLeavesSuccess = rectLayout(nonLeavesLyt, [0,0], newDims, false, false, opts, {subLayoutFn:
				((n,p,d,h,a,o) => sweepLayout(n,p,d,h,allowCollapse,o,{sepArea:sepArea})) as LayoutFn});
			if ((sweptLeft && sepAreaLen > sepArea.dims[1]) || (!sweptLeft && sepAreaLen > sepArea.dims[0])){
				sepAreaUsed = true;
			}
		}
		if (!nonLeavesSuccess){
			if (allowCollapse){
				node.children = [];
				LayoutNode.updateDCounts(node, 1 - node.dCount);
				return oneSqrLayout(node, pos, dims, false, false, opts);
			}
			return false;
		}
		nonLeavesLyt.children.forEach(lyt => {
			lyt.pos[0] += newPos[0];
			lyt.pos[1] += newPos[1];
		});
	}
	// Combine layouts
	if (leavesLyt == null || nonLeavesLyt == null){ //hint for typescript
		return false;
	}
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
	node.assignLayoutData(pos, usedDims, {showHeader, empSpc, sepSweptArea: usingParentArea ? parentArea! : null});
	return true;
}

// Returns [0 ... len]
function range(len: number){
	return [...Array(len).keys()];
}
// Returns sum of array values
function arraySum(array: number[]){
	return array.reduce((x,y) => x+y);
}
// Returns array copy with vals clipped to within [min,max], redistributing to compensate (returns null on failure)
function limitVals(arr: number[], min: number, max: number){
	let vals = [...arr];
	let clipped = new Array(vals.length).fill(false);
	let owedChg = 0; // Stores total change made after clipping values
	while (true){
		// Clip values
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
		// Compensate for changes made
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
// Usable to iterate through possible int arrays with ascending values in the range 0 to maxLen-1, starting with [0]
	// eg: With maxLen 3, updates [0] to [0,1], then to [0,2], then [0,1,2], then null
function updateAscSeq(seq: number[], maxLen: number){
	// Try increasing last element, then preceding elements, then extending the array
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
