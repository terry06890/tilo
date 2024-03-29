/*
 * Used to create tile-based layouts of tree-of-life data.
 *
 * Given a TolNode tree, initLayoutTree() produces a subtree-corresponding
 * LayoutNode tree, on which tryLayout() can run a layout algorithm.
 */

import {TolMap} from './tol';
import {range, arraySum, linspace, limitVals, updateAscSeq} from './util';

// ========== General classes/types ==========

// Represents a node/tree that holds layout data for a TolNode node/tree
export class LayoutNode {
	// TolNode name
	name: string;
	// Tree-structure related
	children: LayoutNode[];
	parent: LayoutNode | null;
	tips: number; // Number of descendant leaf nodes
	depth: number; // Number of ancestor nodes
	// Layout data
	pos: [number, number];
	dims: [number, number];
	showHeader: boolean;
	sepSweptArea: SepSweptArea | null; // Used with layout option 'sweepToParent'
	empSpc: number; // Amount of unused layout space (in pixels)
	// Other
	hidden: boolean; // Used to hide nodes upon an expand-to-view
	hiddenWithVisibleTip: boolean;
	hasFocus: boolean; // Used by search and auto-mode to mark/flash a tile

	// Constructor ('parent' are 'depth' are generally initialised later, 'tips' is computed)
	constructor(name: string, children: LayoutNode[]){
		this.name = name;
		this.children = children;
		this.parent = null;
		this.tips = children.length == 0 ? 1 : arraySum(children.map(n => n.tips));
		this.depth = 0;
		//
		this.pos = [0,0];
		this.dims = [0,0];
		this.showHeader = false;
		this.sepSweptArea = null;
		this.empSpc = 0;
		//
		this.hidden = false;
		this.hiddenWithVisibleTip = false;
		this.hasFocus = false;
	}

	// Returns a new tree with the same structure and names
	// 'chg' is usable to apply a change to the resultant tree
	cloneNodeTree(chg?: LayoutTreeChg | null): LayoutNode {
		let newNode: LayoutNode;
		if (chg != null && this == chg.node){
			switch (chg.type){
				case 'expand': {
					const children = chg.tolMap.get(this.name)!.children.map((n: string) => new LayoutNode(n, []));
					newNode = new LayoutNode(this.name, children);
					newNode.children.forEach(n => {
						n.parent = newNode;
						n.depth = this.depth + 1;
					});
					break;
				}
				case 'collapse': {
					newNode = new LayoutNode(this.name, []);
					break;
				}
			}
		} else {
			const children = this.children.map(n => n.cloneNodeTree(chg));
			newNode = new LayoutNode(this.name, children);
			children.forEach(n => {n.parent = newNode});
		}
		newNode.depth = this.depth;
		return newNode;
	}

	// Copies layout data to a given LayoutNode tree
		// If a target node has more/less children, removes/gives own children
	// If 'map' is provided, it is updated to represent node additions/removals
	copyTreeForRender(target: LayoutNode, map?: LayoutMap | null): void {
		target.pos = this.pos;
		target.dims = this.dims;
		target.showHeader = this.showHeader;
		target.sepSweptArea = this.sepSweptArea;
		target.tips = this.tips; // Copied for structural-consistency
		target.empSpc = this.empSpc; // Note: Currently redundant, but maintains data-consistency
		// Handle children
		if (this.children.length == target.children.length){
			this.children.forEach((n,i) => n.copyTreeForRender(target.children[i], map));
		} else if (this.children.length < target.children.length){
			if (map != null){
				target.children.forEach(child => removeFromLayoutMap(child, map));
			}
			target.children = [];
		} else {
			target.children = this.children;
			target.children.forEach(n => {n.parent = target});
			if (map != null){
				target.children.forEach(child => {addToLayoutMap(child, map)});
			}
		}
	}

	// Assigns layout data to this single node
	assignLayoutData(pos = [0,0] as [number,number], dims = [0,0] as [number,number],
		{showHeader = false, sepSweptArea = null as SepSweptArea | null, empSpc = 0} = {}): void {
		this.pos = [...pos];
		this.dims = [...dims];
		this.showHeader = showHeader;
		this.sepSweptArea = sepSweptArea;
		this.empSpc = empSpc;
	}

	// Given a sequence of child/grandchild/etc names, adds this/the_child's/the_grandchild's/etc children
	addDescendantChain(nameChain: string[], tolMap: TolMap, map?: LayoutMap): void {
		let layoutNode = this as LayoutNode;
		for (const childName of nameChain){
			// Add children
			const tolNode = tolMap.get(layoutNode.name)!;
			layoutNode.children = tolNode.children.map((name: string) => new LayoutNode(name, []));
			layoutNode.children.forEach(node => {
				node.parent = layoutNode;
				node.depth = layoutNode.depth + 1;
				if (map != null){
					map.set(node.name, node);
				}
			});
			LayoutNode.updateTips(layoutNode, layoutNode.children.length - 1);
			// Get matching child node
			const childNode = layoutNode.children.find(n => n.name == childName);
			if (childNode == null){
				throw new Error('Child name not found');
			}
			layoutNode = childNode;
		}
	}

	// Update the 'tips' value of a node and it's ancestors
	static updateTips(node: LayoutNode | null, diff: number): void {
		while (node != null){
			node.tips += diff;
			node = node.parent;
		}
	}

	// Used to hide ancestor/sibling nodes, upon an expand-to-view
	static hideUpward(node: LayoutNode, map: LayoutMap): void {
		if (node.parent != null){
			node.parent.hidden = true;
			node.parent.hiddenWithVisibleTip = true;
			node.parent.children.filter(child => child != node).forEach(sibling => {
				sibling.hidden = true;
				// Remove sibling children from layout tree
				LayoutNode.updateTips(sibling, 1 - sibling.children.length);
				sibling.children.forEach(n => removeFromLayoutMap(n, map));
				sibling.children = [];
			});
			// Recurse
			LayoutNode.hideUpward(node.parent, map);
		}
	}

	// Used to unhide a node and it's descendants
	static showDownward(node: LayoutNode): void {
		if (node.hidden){
			node.hidden = false;
			node.hiddenWithVisibleTip = false;
			node.children.forEach(n => LayoutNode.showDownward(n));
		}
	}
}

// Holds values that affect how layout is done
export type LayoutOptions = {
	tileSpacing: number; // Spacing between tiles, in pixels
	headerSz: number;
	minTileSz: number; // Minimum size of a tile edge, in pixels
	maxTileSz: number;
	// Layout-algorithm related
	layoutType: 'sqr' | 'rect' | 'sweep' | 'sqr-overflow'; // Represents the LayoutFn function to use
	rectMode: 'horz' | 'vert' | 'linear' | 'auto' | 'auto first-row';
		// Rect-layout in 1 row, 1 column, 1 row or column, or multiple rows (optionally with first-row-heuristic)
	rectSensitivity: number; // Between 0 and 1. Higher values mean higher sensitivity to empty space.
	sweepMode: 'left' | 'top' | 'shorter' | 'auto'; // Sweep to left, top, shorter-side, or to minimise empty space
	sweptNodesPrio: 'linear' | 'sqrt' | 'pow-2/3'; // Specifies allocation of space to swept-vs-remaining nodes
	sweepToParent: 'none' | 'prefer' | 'fallback'; // Whether/when to place swept nodes in a parent swept-leaves area
};

// Represents a change to a LayoutNode tree
export type LayoutTreeChg = {
	type: 'expand' | 'collapse';
	node: LayoutNode;
	tolMap: TolMap;
}

// Used with layout option 'sweepToParent', and represents, for a LayoutNode, a parent area to place leaf nodes in
export class SepSweptArea {
	pos: [number, number];
	dims: [number, number];
	sweptLeft: boolean; // True if the parent's leaves were swept left
	used: boolean; // Used by the parent. Set to true by the child if it uses the area.
	constructor(pos: [number, number], dims: [number, number], sweptLeft: boolean, used = false){
		this.pos = pos;
		this.dims = dims;
		this.sweptLeft = sweptLeft;
		this.used = used;
	}
}

// ========== For name-to-node layout maps ==========

// Represents a map from TolNode names to nodes in a LayoutNode tree
export type LayoutMap = Map<string, LayoutNode>;

// Creates a LayoutMap for a LayoutNode tree
export function initLayoutMap(layoutTree: LayoutNode): LayoutMap {
	function helper(node: LayoutNode, map: LayoutMap): void {
		map.set(node.name, node);
		node.children.forEach(n => helper(n, map));
	}
	const map = new Map();
	helper(layoutTree, map);
	return map;
}

// Adds a node and it's descendants' names to a LayoutMap
function addToLayoutMap(node: LayoutNode, map: LayoutMap): void {
	map.set(node.name, node);
	node.children.forEach(n => addToLayoutMap(n, map));
}

// Removes a node and it's descendants' names from a LayoutMap
function removeFromLayoutMap(node: LayoutNode, map: LayoutMap): void {
	map.delete(node.name);
	node.children.forEach(n => removeFromLayoutMap(n, map));
}

// ========== Main layout functions ==========

// Creates a LayoutNode representing a TolNode tree, up to a given depth (0 means just the root, -1 means no limit)
export function initLayoutTree(tolMap: TolMap, rootName: string, depth: number): LayoutNode {
	function initHelper(tolMap: TolMap, nodeName: string, depthLeft: number, atDepth = 0): LayoutNode {
		if (depthLeft == 0){
			const node = new LayoutNode(nodeName, []);
			node.depth = atDepth;
			return node;
		} else {
			const childNames = tolMap.get(nodeName)!.children;
			if (childNames.length == 0 || !tolMap.has(childNames[0])){
				return new LayoutNode(nodeName, []);
			} else {
				const children = childNames.map((name: string) =>
					initHelper(tolMap, name, depthLeft != -1 ? depthLeft-1 : -1, atDepth+1));
				const node = new LayoutNode(nodeName, children);
				children.forEach(n => n.parent = node);
				return node;
			}
		}
	}
	return initHelper(tolMap, rootName, depth);
}

// Attempts layout on a LayoutNode tree, for an area with given width+height
	// If successful, sets fields of the tree's LayoutNodes, and returns true
// 'allowCollapse' allows the layout algorithm to collapse nodes to avoid layout failure
// 'chg' allows for expanding/collapsing a node before performing layout
// 'layoutMap', if provided, is updated with added/removed children
export function tryLayout(
	layoutTree: LayoutNode, dims: [number,number], options: LayoutOptions,
	{allowCollapse = false, chg = null as LayoutTreeChg | null, layoutMap = null as LayoutMap | null} = {}
	): boolean {
	// Create a new LayoutNode tree, in case of layout failure
	const tempTree = layoutTree.cloneNodeTree(chg);
	let success: boolean;
	switch (options.layoutType){
		case 'sqr': success = sqrLayout(tempTree, [0,0], dims, true, allowCollapse, options); break;
		case 'rect': success = rectLayout(tempTree, [0,0], dims, true, allowCollapse, options); break;
		case 'sweep': success = sweepLayout(tempTree, [0,0], dims, true, allowCollapse, options); break;
		case 'sqr-overflow': success = sqrOverflowLayout(tempTree, [0,0], dims, true, allowCollapse, options); break;
	}
	if (success){
		if (options.layoutType != 'sqr-overflow'){
			// Center in layout area
			tempTree.pos[0] += (dims[0] - tempTree.dims[0]) / 2;
			tempTree.pos[1] += (dims[1] - tempTree.dims[1]) / 2;
		}
		// Copy to given LayoutNode tree
		tempTree.copyTreeForRender(layoutTree, layoutMap);
	}
	return success;
}

// ========== Specific layout functions ==========

// Type for functions called by tryLayout() to attempt layout
// Similar parameters to tryLayout(), with 'showHeader' and 'ownOpts' generally used by other LayoutFns
type LayoutFn = (
	node: LayoutNode,
	pos: [number, number],
	dims: [number, number],
	showHeader: boolean,
	allowCollapse: boolean,
	opts: LayoutOptions,
	ownOpts?: any,
) => boolean;

// Lays out node as one square, ignoring child nodes // Used for base cases
const oneSqrLayout: LayoutFn = function (node, pos, dims, showHeader, allowCollapse, opts){
	const tileSz = Math.min(dims[0], dims[1], opts.maxTileSz);
	if (tileSz < opts.minTileSz){
		return false;
	}
	node.assignLayoutData(pos, [tileSz,tileSz], {showHeader, empSpc: dims[0]*dims[1] - tileSz**2});
	return true;
}

// Lays out nodes as squares within a grid, with intervening+surrounding spacing
const sqrLayout: LayoutFn = function (node, pos, dims, showHeader, allowCollapse, opts){
	if (node.children.length == 0){
		return oneSqrLayout(node, pos, dims, false, false, opts);
	}

	// Consider area excluding header and top/left spacing
	const headerSz = showHeader ? opts.headerSz : 0;
	const newPos = [opts.tileSpacing, opts.tileSpacing + headerSz];
	const newDims = [dims[0] - opts.tileSpacing, dims[1] - opts.tileSpacing - headerSz];
	if (newDims[0] * newDims[1] <= 0){
		return false;
	}

	// Find number of rows/columns with least empty space
	const numChildren = node.children.length;
	const areaAR = newDims[0] / newDims[1]; // Aspect ratio
	let lowestEmpSpc = Number.POSITIVE_INFINITY, usedNumCols = 0, usedNumRows = 0, usedTileSz = 0;
	const MAX_TRIES = 50; // If there are many possibilities, skip some
	const ptlNumCols = numChildren == 1 ? [1] :
		linspace(1, numChildren, Math.min(numChildren, MAX_TRIES)).map(n => Math.floor(n));
	for (const numCols of ptlNumCols){
		const numRows = Math.ceil(numChildren / numCols);
		const gridAR = numCols / numRows;
		const usedFrac = // Fraction of area occupied by maximally-fitting grid
			areaAR > gridAR ? gridAR / areaAR : areaAR / gridAR;

		// Get tile edge length
		let tileSz = (areaAR > gridAR ? newDims[1] / numRows : newDims[0] / numCols) - opts.tileSpacing;
		if (tileSz < opts.minTileSz){
			continue;
		} else if (tileSz > opts.maxTileSz){
			tileSz = opts.maxTileSz;
		}

		// Get empty space
		const empSpc = (1 - usedFrac) * (newDims[0] * newDims[1]) + // Area outside grid plus ...
			(numCols * numRows - numChildren) * (tileSz - opts.tileSpacing)**2; // empty cells within grid

		// Compare with best-so-far
		if (empSpc < lowestEmpSpc){
			lowestEmpSpc = empSpc;
			usedNumCols = numCols;
			usedNumRows = numRows;
			usedTileSz = tileSz;
		}
	}

	// Check if unable to find grid
	if (lowestEmpSpc == Number.POSITIVE_INFINITY){
		if (allowCollapse){
			node.children = [];
			LayoutNode.updateTips(node, 1 - node.tips);
			return oneSqrLayout(node, pos, dims, false, false, opts);
		}
		return false;
	}

	// Layout children
	for (let i = 0; i < numChildren; i++){
		const child = node.children[i];
		const childX = newPos[0] + (i % usedNumCols) * (usedTileSz + opts.tileSpacing);
		const childY = newPos[1] + Math.floor(i / usedNumCols) * (usedTileSz + opts.tileSpacing);
		let success: boolean;
		if (child.children.length == 0){
			success = oneSqrLayout(child, [childX,childY], [usedTileSz,usedTileSz], false, false, opts);
		} else {
			success = sqrLayout(child, [childX,childY], [usedTileSz,usedTileSz], true, allowCollapse, opts);
		}
		if (!success){
			if (allowCollapse){
				node.children = [];
				LayoutNode.updateTips(node, 1 - node.tips);
				return oneSqrLayout(node, pos, dims, false, false, opts);
			}
			return false;
		}
	}

	// Create layout
	const usedDims: [number, number] = [
		usedNumCols * (usedTileSz + opts.tileSpacing) + opts.tileSpacing,
		usedNumRows * (usedTileSz + opts.tileSpacing) + opts.tileSpacing + headerSz,
	];
	const empSpc = // Empty space within usedDims area
		(usedNumCols * usedNumRows - numChildren) * (usedTileSz - opts.tileSpacing)**2 +
		arraySum(node.children.map(child => child.empSpc));
	node.assignLayoutData(pos, usedDims, {showHeader, empSpc});
	return true;
}

// Lays out nodes as rows of rectangles, deferring to sqrLayout() or oneSqrLayout() for simpler cases
//'subLayoutFn' allows other LayoutFns to use this layout, but transfer control back to themselves on recursion
const rectLayout: LayoutFn = function (node, pos, dims, showHeader, allowCollapse, opts,
	ownOpts?: {subLayoutFn?: LayoutFn}){
	// Check for simpler cases
	if (node.children.length == 0){
		return oneSqrLayout(node, pos, dims, false, false, opts);
	} else if (node.children.every(n => n.children.length == 0)){
		return sqrLayout(node, pos, dims, showHeader, allowCollapse, opts);
	}

	// Consider area excluding header and top/left spacing
	const headerSz = showHeader ? opts.headerSz : 0;
	const newPos = [opts.tileSpacing, opts.tileSpacing + headerSz];
	const newDims = [dims[0] - opts.tileSpacing, dims[1] - opts.tileSpacing - headerSz];
	if (newDims[0] * newDims[1] < node.tips * (opts.minTileSz + opts.tileSpacing)**2){
		if (allowCollapse){
			node.children = [];
			LayoutNode.updateTips(node, 1 - node.tips);
			return oneSqrLayout(node, pos, dims, false, false, opts);
		}
		return false;
	}

	// Try finding arrangement with low empty space
	// Done by searching possible row-groupings, allocating within rows using 'tips' vals, and trimming empty space
	const numChildren = node.children.length;
	let rowBrks: number[] = []; // Will hold indices for nodes at which each row starts
	let lowestEmpSpc = Number.POSITIVE_INFINITY;
	let usedTree: LayoutNode | null = null; // Best-so-far layout
	let usedEmpRight = 0, usedEmpBottom = 0; // usedTree's empty-space at-right-of-all-rows and below-last-row
	const minCellDims = [
		opts.minTileSz + opts.tileSpacing +
			(opts.layoutType == 'sweep' ? opts.tileSpacing*2 : 0), // Can situationally assume non-leaf children
		opts.minTileSz + opts.tileSpacing +
			(opts.layoutType == 'sweep' ? opts.tileSpacing*2 + opts.headerSz : 0)
	];
	RowBrksLoop:
	while (true){
		// Update rowBrks or exit loop
		switch (opts.rectMode){
			case 'horz':
				if (rowBrks.length == 0){
					rowBrks = [0];
				} else {
					break RowBrksLoop;
				}
				break;
			case 'vert':
				if (rowBrks.length == 0){
					rowBrks = range(numChildren);
				} else {
					break RowBrksLoop;
				}
				break;
			case 'linear':
				if (rowBrks.length == 0){
					rowBrks = [0];
				} else if (rowBrks.length == numChildren){
					rowBrks = range(numChildren);
				} else {
					break RowBrksLoop;
				}
				break;
			case 'auto':
				if (rowBrks.length == 0){
					rowBrks = [0];
				} else {
					const updated = updateAscSeq(rowBrks, numChildren);
					if (!updated){
						break RowBrksLoop;
					}
				}
				break;
			case 'auto first-row': // Like auto, but only iterates over first-rows, determining the rest with 'tips' vals
				if (rowBrks.length == 0){
					rowBrks = [0];
				} else {
					// Get next possible first row
					const idxFirstRowLastEl = (rowBrks.length == 1 ? numChildren : rowBrks[1]) - 1;
					if (idxFirstRowLastEl == 0){
						break RowBrksLoop;
					}
					rowBrks = [0];
					rowBrks.push(idxFirstRowLastEl);
					// Allocate remaining rows
					const firstRowTips = arraySum(range(rowBrks[1]).map(idx => node.children[idx].tips));
					let tipsTotal = node.children[idxFirstRowLastEl].tips;
					let nextRowIdx = idxFirstRowLastEl + 1;
					while (nextRowIdx < numChildren){ // Over potential next row breaks
						const nextTipsTotal = tipsTotal + node.children[nextRowIdx].tips;
						if (nextTipsTotal <= firstRowTips){ // If acceptable within current row
							tipsTotal = nextTipsTotal;
						} else {
							rowBrks.push(nextRowIdx);
							tipsTotal = node.children[nextRowIdx].tips;
						}
						nextRowIdx++;
					}
				}
				break;
		}

		// Create array-of-arrays representing each rows' cells' 'tips' values
		const rowsOfCnts: number[][] = new Array(rowBrks.length);
		for (let rowIdx = 0; rowIdx < rowBrks.length; rowIdx++){
			const numNodes = (rowIdx < rowBrks.length - 1) ?
				rowBrks[rowIdx + 1] - rowBrks[rowIdx] :
				numChildren - rowBrks[rowIdx];
			const rowNodeIdxs = range(numNodes).map(i => i + rowBrks![rowIdx]);
			rowsOfCnts[rowIdx] = rowNodeIdxs.map(idx => node.children[idx].tips);
		}

		// Get initial cell dims
		const cellWs: number[][] = new Array(rowsOfCnts.length);
		for (let rowIdx = 0; rowIdx < rowsOfCnts.length; rowIdx++){
			const rowCount = arraySum(rowsOfCnts[rowIdx]);
			cellWs[rowIdx] = range(rowsOfCnts[rowIdx].length).map(
				colIdx => rowsOfCnts[rowIdx][colIdx] / rowCount * newDims[0]);
		}
		const totalTips = arraySum(node.children.map(n => n.tips));
		let cellHs = rowsOfCnts.map(rowOfCnts => arraySum(rowOfCnts) / totalTips * newDims[1]);

		// Check min-tile-size, attempting to reallocate space if needed
		for (let rowIdx = 0; rowIdx < rowsOfCnts.length; rowIdx++){
			const newWs = limitVals(cellWs[rowIdx], minCellDims[0], Number.POSITIVE_INFINITY);
			if (newWs == null){
				continue RowBrksLoop;
			}
			cellWs[rowIdx] = newWs;
		}
		cellHs = limitVals(cellHs, minCellDims[1], Number.POSITIVE_INFINITY)!;
		if (cellHs == null){
			continue RowBrksLoop;
		}

		// Get cell xy-coordinates
		const cellXs: number[][] = new Array(rowsOfCnts.length);
		for (let rowIdx = 0; rowIdx < rowBrks.length; rowIdx++){
			cellXs[rowIdx] = [0];
			for (let colIdx = 1; colIdx < rowsOfCnts[rowIdx].length; colIdx++){
				cellXs[rowIdx].push(cellXs[rowIdx][colIdx - 1] + cellWs[rowIdx][colIdx - 1]);
			}
		}
		const cellYs: number[] = new Array(rowsOfCnts.length).fill(0);
		for (let rowIdx = 1; rowIdx < rowBrks.length; rowIdx++){
			cellYs[rowIdx] = cellYs[rowIdx - 1] + cellHs[rowIdx - 1];
		}

		// Determine child layouts, resizing cells to reduce empty space
		const tempTree: LayoutNode = node.cloneNodeTree();
		let empRight = Number.POSITIVE_INFINITY, empBottom = 0;
		for (let rowIdx = 0; rowIdx < rowBrks.length; rowIdx++){
			for (let colIdx = 0; colIdx < rowsOfCnts[rowIdx].length; colIdx++){
				const nodeIdx = rowBrks[rowIdx] + colIdx;
				const child: LayoutNode = tempTree.children[nodeIdx];
				const childPos: [number, number] = [newPos[0] + cellXs[rowIdx][colIdx], newPos[1] + cellYs[rowIdx]];
				const childDims: [number, number] = [
					cellWs[rowIdx][colIdx] - opts.tileSpacing,
					cellHs[rowIdx] - opts.tileSpacing
				];
				let success: boolean;
				if (child.children.length == 0){
					success = oneSqrLayout(child, childPos, childDims, false, false, opts);
				} else if (child.children.every(n => n.children.length == 0)){
					success = sqrLayout(child, childPos, childDims, true, allowCollapse, opts);
				}  else {
					const layoutFn = (ownOpts && ownOpts.subLayoutFn) || rectLayout;
					success = layoutFn(child, childPos, childDims, true, allowCollapse, opts);
				}
				if (!success){
					continue RowBrksLoop;
				}
				// Remove horizontal empty space by trimming cell and moving/expanding any next cell
				const horzEmp = childDims[0] - child.dims[0];
				cellWs[rowIdx][colIdx] -= horzEmp;
				if (colIdx < rowsOfCnts[rowIdx].length - 1){
					cellXs[rowIdx][colIdx + 1] -= horzEmp;
					cellWs[rowIdx][colIdx + 1] += horzEmp;
				} else {
					empRight = Math.min(empRight, horzEmp);
				}
			}
			// Remove vertical empty space by trimming row and moving/expanding any next row
			const childUsedHs = range(rowsOfCnts[rowIdx].length).map(
				colIdx => tempTree.children[rowBrks[rowIdx] + colIdx].dims[1]);
			const vertEmp = cellHs[rowIdx] - opts.tileSpacing - Math.max(...childUsedHs);
			cellHs[rowIdx] -= vertEmp;
			if (rowIdx < rowBrks.length - 1){
				cellYs[rowIdx + 1] -= vertEmp;
				cellHs[rowIdx + 1] += vertEmp;
			} else {
				empBottom = vertEmp;
			}
		}

		// Get empty space
		const usedSpc = arraySum(tempTree.children.map(
			child => (child.dims[0] + opts.tileSpacing) * (child.dims[1] + opts.tileSpacing) - child.empSpc));
		const empSpc = newDims[0] * newDims[1] - usedSpc;

		// Check with best-so-far
		if (empSpc < lowestEmpSpc * opts.rectSensitivity){
			lowestEmpSpc = empSpc;
			usedTree = tempTree;
			usedEmpRight = empRight;
			usedEmpBottom = empBottom;
		}
	}

	// Check if no found layout
	if (usedTree == null){
		if (allowCollapse){
			node.children = [];
			LayoutNode.updateTips(node, 1 - node.tips);
			return oneSqrLayout(node, pos, dims, false, false, opts);
		}
		return false;
	}

	// Create layout
	usedTree.copyTreeForRender(node);
	const usedDims: [number, number] = [dims[0] - usedEmpRight, dims[1] - usedEmpBottom];
	node.assignLayoutData(pos, usedDims, {showHeader, empSpc: lowestEmpSpc});
	return true;
}

// Lays out nodes by pushing leaves to one side, and using rectLayout() for the non-leaves
// With layout option 'sweepToParent', leaves from child nodes may occupy a parent's leaf-section
// 'sepArea' represents a usable leaf-section area from a direct parent,
	// and is changed to represent the area used, with those changes visible to the parent for reducing empty space
const sweepLayout: LayoutFn = function (node, pos, dims, showHeader, allowCollapse, opts,
	ownOpts?: {sepArea?: SepSweptArea}){
	// Separate leaf and non-leaf nodes
	const leaves: LayoutNode[] = [], nonLeaves: LayoutNode[] = [];
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
	const headerSz = showHeader ? opts.headerSz : 0;
	let leavesLyt: LayoutNode | null = null, nonLeavesLyt: LayoutNode | null = null, sweptLeft = false;
	let sepArea: SepSweptArea | null = null; // Represents leaf-section area provided for a child
	const haveParentArea = ownOpts != null && ownOpts.sepArea != null;
	let trySweepToParent = haveParentArea && opts.sweepToParent == 'prefer';

	// Using a loop for conditionally retrying layout
	while (true){
		if (!trySweepToParent){ // Try laying-out normally
			// Choose proportion of area to use for leaves
			let ratio: number; // area-for-leaves / area-for-non-leaves
			const nonLeavesTiles = arraySum(nonLeaves.map(n => n.tips));
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
			const newPos = [0, headerSz];
			const newDims: [number,number] = [dims[0], dims[1] - headerSz];
			leavesLyt = new LayoutNode('SWEEP_' + node.name, leaves);
				// Note: Intentionally neglecting to update child nodes' 'parent' or 'depth' fields here
			const minSz = opts.minTileSz + opts.tileSpacing*4;
			const sweptW = Math.min(Math.max(minSz, newDims[0] * ratio), newDims[0] - minSz);
			const sweptH = Math.min(Math.max(minSz, newDims[1] * ratio), newDims[0] - minSz);
			let leavesSuccess: boolean;
			switch (opts.sweepMode){
				case 'left': {
					leavesSuccess = sqrLayout(leavesLyt, [0,0], [sweptW, newDims[1]], false, false, opts);
					sweptLeft = true;
					break;
				}
				case 'top': {
					leavesSuccess = sqrLayout(leavesLyt, [0,0], [newDims[0], sweptH], false, false, opts);
					sweptLeft = false;
					break;
				}
				case 'shorter': {
					const documentAR = document.documentElement.clientWidth / document.documentElement.clientHeight;
					if (documentAR >= 1){
						leavesSuccess = sqrLayout(leavesLyt, [0,0], [sweptW, newDims[1]], false, false, opts);
						sweptLeft = true;
					} else {
						leavesSuccess = sqrLayout(leavesLyt, [0,0], [newDims[0], sweptH], false, false, opts);
						sweptLeft = false;
					}
					break;
				}
				case 'auto': {
					// Attempt left-sweep, then top-sweep on a copy, and copy over if better
					leavesSuccess = sqrLayout(leavesLyt, [0,0], [sweptW, newDims[1]], false, false, opts);
					sweptLeft = true;
					const tempTree = leavesLyt.cloneNodeTree();
					const sweptTopSuccess = sqrLayout(tempTree, [0,0], [newDims[0], sweptH], false, false, opts);
					if (sweptTopSuccess && (!leavesSuccess || tempTree.empSpc < leavesLyt.empSpc)){
						tempTree.copyTreeForRender(leavesLyt);
						sweptLeft = false;
						leavesSuccess = true;
					}
					break;
				}
			}

			if (leavesSuccess){
				leavesLyt.children.forEach(lyt => {lyt.pos[1] += headerSz});

				// Attempt non-leaves layout
				if (sweptLeft){
					newPos[0] += leavesLyt.dims[0] - opts.tileSpacing;
					newDims[0] += -leavesLyt.dims[0] + opts.tileSpacing;
				} else {
					newPos[1] += leavesLyt.dims[1] - opts.tileSpacing;
					newDims[1] += -leavesLyt.dims[1] + opts.tileSpacing
				}
				nonLeavesLyt = new LayoutNode('SWEEP_REM_' + node.name, nonLeaves);
				let nonLeavesSuccess: boolean;
				if (nonLeaves.length > 1){
					nonLeavesSuccess = rectLayout(nonLeavesLyt, [0,0], newDims, false, false, opts, {subLayoutFn:
						((n,p,d,h,a,o) => sweepLayout(n,p,d,h,allowCollapse,o,{sepArea:sepArea})) as LayoutFn});
				} else {
					if (opts.sweepToParent){
						// Get leftover area usable for non-leaf child's leaves
						if (sweptLeft){
							sepArea = new SepSweptArea(
								[-leavesLyt.dims[0] + opts.tileSpacing,
									leavesLyt.dims[1] - opts.tileSpacing], // Position is relative to child
								[leavesLyt.dims[0], newDims[1] - leavesLyt.dims[1] - opts.tileSpacing],
								sweptLeft
							);
						} else {
							sepArea = new SepSweptArea(
								[leavesLyt.dims[0] - opts.tileSpacing, -leavesLyt.dims[1] + opts.tileSpacing],
								[newDims[0] - leavesLyt.dims[0] - opts.tileSpacing, leavesLyt.dims[1]],
								sweptLeft
							);
						}
					}
					// Attempt layout
					nonLeavesSuccess = rectLayout(nonLeavesLyt, [0,0], newDims, false, false, opts, {subLayoutFn:
						((n,p,d,h,a,o) => sweepLayout(n,p,d,h,allowCollapse,o,{sepArea:sepArea})) as LayoutFn});
				}

				if (nonLeavesSuccess){
					nonLeavesLyt.children.forEach(lyt => {
						lyt.pos[0] += newPos[0];
						lyt.pos[1] += newPos[1];
					});

					// Create combined layout
					let usedDims: [number, number];
					if (sweptLeft){
						usedDims = [
							leavesLyt.dims[0] + nonLeavesLyt.dims[0] - opts.tileSpacing,
							Math.max(leavesLyt.dims[1] + (sepArea != null && sepArea.used ? sepArea.dims[1] : 0),
								nonLeavesLyt.dims[1]) + headerSz
						];
					} else {
						usedDims = [
							Math.max(leavesLyt.dims[0] + (sepArea != null && sepArea.used ? sepArea.dims[0] : 0),
								nonLeavesLyt.dims[0]),
							leavesLyt.dims[1] + nonLeavesLyt.dims[1] - opts.tileSpacing + headerSz
						];
					}
					const empSpc = leavesLyt.empSpc + nonLeavesLyt.empSpc;
					node.assignLayoutData(pos, usedDims, {showHeader, empSpc, sepSweptArea: null});
					return true;
				}
			}
			if (haveParentArea && opts.sweepToParent == 'fallback'){
				trySweepToParent = true;
				continue;
			}
			break;
		} else { // Try using parent-provided area
			const parentArea = ownOpts!.sepArea!;

			// Attempt leaves layout
			sweptLeft = parentArea.sweptLeft;
			leavesLyt = new LayoutNode('SWEEP_' + node.name, leaves);
			const leavesSuccess = sqrLayout(leavesLyt, [0,0], parentArea.dims, !sweptLeft, false, opts);
			let nonLeavesSuccess = true;

			if (leavesSuccess){
				// Attempt non-leaves layout
				const newDims: [number,number] = [dims[0], dims[1] - (sweptLeft ? headerSz : 0)];
				nonLeavesLyt = new LayoutNode('SWEEP_REM_' + node.name, nonLeaves);
				if (nonLeaves.length > 1){
					nonLeavesSuccess = rectLayout(nonLeavesLyt, [0,0], newDims, false, false, opts, {subLayoutFn:
						((n,p,d,h,a,o) => sweepLayout(n,p,d,h,allowCollapse,o,{sepArea:sepArea})) as LayoutFn});
				} else {
					// Get leftover area usable for non-leaf child's leaves
					if (sweptLeft){
						sepArea = new SepSweptArea(
							[parentArea.pos[0], parentArea.pos[1] + leavesLyt.dims[1] - (opts.tileSpacing + headerSz)],
								// Position is made relative to a non-leaf child
							[parentArea.dims[0], parentArea.dims[1] - leavesLyt.dims[1] - opts.tileSpacing*2],
							sweptLeft, false
						);
					} else {
						sepArea = new SepSweptArea(
							[parentArea.pos[0] + leavesLyt.dims[0] - opts.tileSpacing, parentArea.pos[1] + headerSz],
							[parentArea.dims[0] - leavesLyt.dims[0] - opts.tileSpacing*2, parentArea.dims[1] - headerSz],
							sweptLeft, false
						);
					}
					// Attempt layout
					nonLeavesSuccess = rectLayout(nonLeavesLyt, [0,0], newDims, false, false, opts, {subLayoutFn:
						((n,p,d,h,a,o) => sweepLayout(n,p,d,h,allowCollapse,o,{sepArea:sepArea})) as LayoutFn});
				}

				if (nonLeavesSuccess){
					// Adjust non-leaf child positions
					if (sweptLeft){
						nonLeavesLyt.children.forEach(lyt => {lyt.pos[1] += headerSz});
					}

					// Update parentArea to represent space used
					parentArea.used = true;
					if (sweptLeft){
						parentArea.dims[1] = leavesLyt.dims[1];
						let newX = parentArea.pos[0] + (parentArea.dims[0] - leavesLyt.dims[0]);
						let newW = leavesLyt.dims[0];
						if (sepArea != null && sepArea.used){
							parentArea.dims[1] += sepArea.dims[1] + opts.tileSpacing;
							if (sepArea.dims[0] + opts.tileSpacing > leavesLyt.dims[0]){
								newX = parentArea.pos[0] + (parentArea.dims[0] - sepArea.dims[0] - opts.tileSpacing);
								newW = sepArea.dims[0] + opts.tileSpacing;
							}
						}
						// Shrink to avoid excess space between leaves and non-leaves
						parentArea.pos[0] = newX;
						parentArea.dims[0] = newW;
					} else {
						parentArea.dims[0] = leavesLyt.dims[0];
						if (sepArea != null && sepArea.used){
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

					// Move leaves to parent area
					leavesLyt.children.map(lyt => {
						lyt.pos[0] += parentArea!.pos[0];
						lyt.pos[1] += parentArea!.pos[1];
					});

					const usedDims: [number,number] = [nonLeavesLyt.dims[0], nonLeavesLyt.dims[1] + (sweptLeft ? headerSz : 0)];
					node.assignLayoutData(pos, usedDims, {showHeader, empSpc: nonLeavesLyt.empSpc, sepSweptArea: parentArea});
					return true;
				}
			}
			if (nonLeavesSuccess == true && opts.sweepToParent == 'prefer'){
				trySweepToParent = false;
				continue;
			}
			break;
		}
	}

	// Handle layout-failure
	if (allowCollapse){
		node.children = [];
		LayoutNode.updateTips(node, 1 - node.tips);
		return oneSqrLayout(node, pos, dims, false, false, opts);
	}
	return false;
}

// Lays out nodes like sqrLayout(), but may extend past the height limit to fit nodes,
	// and does not recurse on child nodes with children
const sqrOverflowLayout: LayoutFn = function(node, pos, dims, showHeader, allowCollapse, opts){
	if (node.children.length == 0){
		return oneSqrLayout(node, pos, dims, false, false, opts);
	}

	// Consider area excluding header and top/left spacing
	const headerSz = showHeader ? opts.headerSz : 0;
	const newPos = [opts.tileSpacing, opts.tileSpacing + headerSz];
	const newWidth = dims[0] - opts.tileSpacing;
	if (newWidth <= 0){
		return false;
	}

	// Find number of rows and columns
	const numChildren = node.children.length;
	const maxNumCols = Math.floor(newWidth / (opts.minTileSz + opts.tileSpacing));
	if (maxNumCols == 0){
		if (allowCollapse){
			node.children = [];
			LayoutNode.updateTips(node, 1 - node.tips);
			return oneSqrLayout(node, pos, dims, false, false, opts);
		}
		return false;
	}
	const numCols = Math.min(numChildren, maxNumCols);
	const numRows = Math.ceil(numChildren / numCols);
	const tileSz = Math.min(opts.maxTileSz, Math.floor(newWidth / numCols) - opts.tileSpacing);

	// Layout children
	for (let i = 0; i < numChildren; i++){
		const childX = newPos[0] + (i % numCols) * (tileSz + opts.tileSpacing);
		const childY = newPos[1] + Math.floor(i / numCols) * (tileSz + opts.tileSpacing);
		oneSqrLayout(node.children[i], [childX,childY], [tileSz,tileSz], false, false, opts);
	}

	const usedDims: [number, number] = [
		numCols * (tileSz + opts.tileSpacing) + opts.tileSpacing,
		numRows * (tileSz + opts.tileSpacing) + opts.tileSpacing + headerSz
	];
	const empSpc = 0; // Intentionally not used
	node.assignLayoutData(pos, usedDims, {showHeader, empSpc});
	return true;
}
