import {TolNode} from './types';

export class LayoutTree {
	root: LayoutNode;
	options: LayoutOptions;
	constructor(tol: TolNode, depth: number, options: LayoutOptions){
		this.root = this.initHelper(tol, depth);
		this.options = options;
	}
	initHelper(tolNode: TolNode, depth: number): LayoutNode {
		if (depth > 0){
			let children = tolNode.children.map(
				(n: TolNode) => this.initHelper(n, depth-1));
			let node = new LayoutNode(tolNode, children);
			children.forEach(n => n.parent = node);
			return node;
		} else {
			return new LayoutNode(tolNode, []);
		}
	}
	tryLayout(pos: [number,number], dims: [number,number]){
		let newLayout: LayoutNode | null;
		switch (this.options.layoutType){
			case 'sqr':   newLayout =   sqrLayoutFn(this.root, pos, dims, false, this.options); break;
			case 'rect':  newLayout =  rectLayoutFn(this.root, pos, dims, false, this.options); break;
			case 'sweep': newLayout = sweepLayoutFn(this.root, pos, dims, false, this.options); break;
		}
		if (newLayout == null)
			return false;
		this.copyTreeForRender(newLayout, this.root);
		return true;
	}
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
	copyTreeForRender(node: LayoutNode, target: LayoutNode): void {
		target.pos = node.pos;
		target.dims = node.dims;
		target.showHeader = node.showHeader;
		target.sepSweptArea = node.sepSweptArea;
		//these are arguably redundant
		target.dCount = node.dCount;
		target.usedDims = node.usedDims;
		target.empSpc = node.empSpc;
		//recurse on children
		node.children.forEach((n,i) => this.copyTreeForRender(n, target.children[i]));
	}
	updateDCounts(node: LayoutNode | null, diff: number): void{
		while (node != null){
			node.dCount += diff;
			node = node.parent;
		}
	}
}
export type LayoutOptions = {
	tileSpacing: number;
	//showHeader: 'all' | 'non-root' | 'expanded' | 'expanded non-root' | 'leaf' | 'none'?
	headerSz: number;
	minTileSz: number;
	maxTileSz: number;
	layoutType: 'sqr' | 'rect' | 'sweep';
	rectMode: 'horz' | 'vert' | 'linear' | 'auto';
	rectSpaceShifting: boolean;
	sweepMode: 'left' | 'top' | 'shorter' | 'auto';
	sweepingToParent: boolean;
};
export class LayoutNode {
	//structure-related
	tolNode: TolNode;
	children: LayoutNode[];
	parent: LayoutNode | null;
	//used for rendering
	pos: [number, number];
	dims: [number, number];
	showHeader: boolean;
	sepSweptArea: SepSweptArea | null;
	//used for layout heuristics
	dCount: number; //number of descendant leaf nodes
	usedDims: [number, number];
	empSpc: number;
	//
	constructor(
		tolNode: TolNode, children: LayoutNode[], pos=[0,0] as [number,number], dims=[0,0] as [number,number],
		{showHeader=false, sepSweptArea=null as SepSweptArea|null, usedDims=[0,0] as [number,number], empSpc=0} = {}){
		this.tolNode = tolNode;
		this.children = children;
		this.parent = null;
		this.pos = pos;
		this.dims = dims;
		this.showHeader = showHeader;
		this.sepSweptArea = sepSweptArea;
		this.dCount = children.length == 0 ? 1 : children.map(n => n.dCount).reduce((x,y) => x+y);
		this.usedDims = usedDims;
		this.empSpc = empSpc;
	}
}
export class SepSweptArea {
	pos: [number, number];
	dims: [number, number];
	sweptLeft: boolean;
	constructor(pos: [number, number], dims: [number, number], sweptLeft: boolean, tileSpacing: number){
		this.pos = pos;
		this.dims = dims;
		this.sweptLeft = sweptLeft;
	}
}

type LayoutFn = (node: LayoutNode, pos: [number, number], dims: [number, number], showHeader: boolean,
	opts: LayoutOptions, ownOpts?: {subLayoutFn?: LayoutFn, sepSweptArea?: SepSweptArea|null}) => LayoutNode | null;

//lays out nodes as squares in a rectangle, with spacing
let sqrLayoutFn: LayoutFn = function (node, pos, dims, showHeader, opts){
	//get number-of-columns with lowest leftover empty space
	let headerSz = showHeader ? opts.headerSz : 0;
	let availW = dims[0] - opts.tileSpacing, availH = dims[1] - headerSz - opts.tileSpacing;
	if (availW*availH <= 0)
		return null;
	let numChildren = node.children.length, ar = availW/availH;
	let lowestEmp = Number.POSITIVE_INFINITY, numCols = 0, numRows = 0, tileSize = 0;
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
		if (empSpc < lowestEmp){
			lowestEmp = empSpc;
			numCols = nc;
			numRows = nr;
			tileSize = tileSz;
		}
	}
	if (lowestEmp == Number.POSITIVE_INFINITY)
		return null;
	let childLayouts = arrayOf(null, numChildren);
	for (let i = 0; i < numChildren; i++){
		let child = node.children[i];
		let childX = opts.tileSpacing + (i % numCols)*(tileSize + opts.tileSpacing);
		let childY = opts.tileSpacing + headerSz + Math.floor(i / numCols)*(tileSize + opts.tileSpacing);
		if (child.children.length == 0){
			childLayouts[i] = new LayoutNode(child.tolNode, [], [childX,childY], [tileSize,tileSize],
				{usedDims: [tileSize,tileSize], empSpc: 0});
		} else {
			childLayouts[i] = sqrLayoutFn(child, [childX,childY], [tileSize,tileSize], true, opts);
			if (childLayouts[i] == null)
				return null;
			lowestEmp += childLayouts[i].empSpc;
		}
	}
	let newNode = new LayoutNode(node.tolNode, childLayouts, pos, dims, {
		showHeader,
		usedDims: [numCols * (tileSize + opts.tileSpacing) + opts.tileSpacing,
			numRows * (tileSize + opts.tileSpacing) + opts.tileSpacing + headerSz],
		empSpc: lowestEmp,
	});
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
	let lowestEmp = Number.POSITIVE_INFINITY, rowBreaks = null, childLayouts = null;
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
		let rowsOfCnts: number[][] = arrayOf([], rowBrks.length);
		for (let r = 0; r < rowBrks.length; r++){
			let numNodes = (r == rowBrks.length-1) ? numChildren-rowBrks[r] : rowBrks[r+1]-rowBrks[r];
			let rowNodeIdxs = seq(numNodes).map(i => i+rowBrks![r]);
			rowsOfCnts[r] = rowNodeIdxs.map(idx => node.children[idx].dCount);
		}
		//get cell dims
		let totalTileCount = node.children.map(n => n.dCount).reduce((x,y) => x+y);
		let cellHs = rowsOfCnts.map(row => row.reduce((x,y) => x+y) / totalTileCount * availH);
		let cellWs = arrayOf(0, numChildren);
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
		let cellXs = arrayOf(0, cellWs.length);
		for (let r = 0; r < rowBrks.length; r++){
			for (let c = 1; c < rowsOfCnts[r].length; c++){
				let nodeIdx = rowBrks[r]+c;
				cellXs[nodeIdx] = cellXs[nodeIdx-1] + cellWs[nodeIdx-1];
			}
		}
		let cellYs = arrayOf(0, cellHs.length);
		for (let r = 1; r < rowBrks.length; r++){
			cellYs[r] = cellYs[r-1] + cellHs[r-1];
		}
		//get child layouts and empty-space
		let childLyts = arrayOf(null, numChildren);
		let empVTotal = 0, empSpc = 0;
		for (let r = 0; r < rowBrks.length; r++){
			let empHorzTotal = 0;
			for (let c = 0; c < rowsOfCnts[r].length; c++){
				let nodeIdx = rowBrks[r]+c;
				let child = node.children[nodeIdx];
				let childX = cellXs[nodeIdx] + opts.tileSpacing, childY = cellYs[r] + opts.tileSpacing + headerSz,
					childW = cellWs[nodeIdx] - opts.tileSpacing, childH = cellHs[r] - opts.tileSpacing;
				if (child.children.length == 0){
					let contentSz = Math.min(childW, childH);
					childLyts[nodeIdx] = new LayoutNode(child.tolNode, [], [childX,childY], [childW,childH],
						{usedDims: [contentSz,contentSz], empSpc: childW*childH - contentSz**2})
				} else if (child.children.every(n => n.children.length == 0)){
					childLyts[nodeIdx] = sqrLayoutFn(child, [childX,childY], [childW,childH], true, opts);
				} else {
					let layoutFn = (ownOpts && ownOpts.subLayoutFn) || rectLayoutFn;
					childLyts[nodeIdx] = layoutFn(child, [childX,childY], [childW,childH], true, opts);
				}
				if (childLyts[nodeIdx] == null)
					continue rowBrksLoop;
				//handle horizontal empty-space-shifting
				if (opts.rectSpaceShifting){
					let empHorz = childLyts[nodeIdx].dims[0] - childLyts[nodeIdx].usedDims[0];
					childLyts[nodeIdx].dims[0] -= empHorz;
					childLyts[nodeIdx].empSpc -= empHorz * childLyts[nodeIdx].dims[1];
					if (c < rowsOfCnts[r].length-1){
						cellXs[nodeIdx+1] -= empHorz;
						cellWs[nodeIdx+1] += empHorz;
					} else {
						empHorzTotal = empHorz;
					}
				}
			}
			//handle vertical empty-space-shifting
			if (opts.rectSpaceShifting){
				let nodeIdxs = seq(rowsOfCnts[r].length).map(i => rowBrks![r]+i);
				let empVerts = nodeIdxs.map(idx => childLyts[idx].dims[1] - childLyts[idx].usedDims[1]);
				let minEmpVert = Math.min(...empVerts);
				nodeIdxs.forEach(idx => {
					childLyts[idx].dims[1] -= minEmpVert;
					childLyts[idx].empSpc -= minEmpVert * childLyts[idx].dims[0];
				});
				if (r < rowBrks.length-1){
					cellYs[r+1] -= minEmpVert;
					cellHs[r+1] += minEmpVert;
				} else {
					empVTotal = minEmpVert;
				}
			}
			//other updates
			empSpc += empHorzTotal * childLyts[rowBrks[r]].dims[1];
		}
		//get empty-space
		for (let r = 0; r < rowBrks.length; r++){
			for (let c = 0; c < rowsOfCnts[r].length; c++){
				empSpc += childLyts[rowBrks[r]+c].empSpc;
			}
		}
		empSpc += empVTotal * availW;
		//check with best-so-far
		if (empSpc < lowestEmp){
			lowestEmp = empSpc;
			rowBreaks = [...rowBrks];
			childLayouts = childLyts;
		}
	}
	if (rowBreaks == null || childLayouts == null) //redundant hinting for tsc
		return null;
	//make no-child tiles have width/height fitting their content
	childLayouts.filter(l => l.children.length == 0).forEach(l => {
		l.dims[0] = l.usedDims[0];
		l.dims[1] = l.usedDims[1];
	});
	//determine layout
	let newNode = new LayoutNode(node.tolNode, childLayouts, pos, dims,
		{showHeader, usedDims: dims, empSpc: lowestEmp});
		//trying to shrink usedDims causes problems with swept-to-parent-area div-alignment
	childLayouts.forEach(n => n.parent = newNode);
	return newNode;
}
//lays out nodes by pushing leaves to one side, partially using other layouts for children
let sweepLayoutFn: LayoutFn = function (node, pos, dims, showHeader, opts, ownOpts={sepSweptArea: null}){
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
		let ratio = leaves.length / (leaves.length + nonLeaves.map(n => n.dCount).reduce((x,y) => x+y));
		let headerSz = showHeader ? opts.headerSz : 0;
		let sweptLayout = null, nonLeavesLayout = null, sweptLeft = false;
		//get swept-area layout
		let parentArea = ownOpts && ownOpts.sepSweptArea, usingParentArea = false;
		if (opts.sweepingToParent && parentArea){
			tempTree = new LayoutNode(new TolNode('SWEEP_' + node.tolNode.name), leaves);
				//not updating the children to point to tempTree as a parent seems acceptable here
			sweptLeft = parentArea.sweptLeft;
			sweptLayout = sqrLayoutFn(tempTree, [0,0], parentArea.dims, sweptLeft, opts);
			if (sweptLayout != null){
				//move leaves to parent area
				sweptLayout.children.map(n => {
					n.pos[0] += parentArea!.pos[0];
					n.pos[1] += parentArea!.pos[1];
				});
				//get remaining-area layout
				let newDims: [number,number] = [dims[0], dims[1] - (sweptLeft ? headerSz : 0)];
				tempTree = new LayoutNode(new TolNode('SWEEP_REM_' + node.tolNode.name), nonLeaves);
				if (nonLeaves.length > 1){
					nonLeavesLayout = rectLayoutFn(tempTree, [0,0], newDims, false, opts,
						{subLayoutFn: sweepLayoutFn});
				} else {
					//get leftover swept-layout-area to propagate
					let leftOverWidth = parentArea.dims[0] - sweptLayout.usedDims[0];
					let leftOverHeight = parentArea.dims[1] - sweptLayout.usedDims[1];
					let leftoverArea = sweptLeft ?
						new SepSweptArea(
							[parentArea.pos[0], parentArea.pos[1]+sweptLayout.usedDims[1]-opts.tileSpacing-headerSz],
							[parentArea.dims[0], leftOverHeight-opts.tileSpacing], sweptLeft) :
						new SepSweptArea(
							[parentArea.pos[0]+sweptLayout.usedDims[0]-opts.tileSpacing, parentArea.pos[1]+headerSz],
							[leftOverWidth-opts.tileSpacing, parentArea.dims[1]-headerSz], sweptLeft);
					//generate layout
					nonLeavesLayout = rectLayoutFn(tempTree, [0,0], newDims, false, opts,
						{subLayoutFn: (n,p,d,h,o) => sweepLayoutFn(n,p,d,h,o,{sepSweptArea:leftoverArea})});
				}
				if (nonLeavesLayout != null){
					nonLeavesLayout.children.forEach(layout => {layout.pos[1] += (sweptLeft ? headerSz : 0)});
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
				xyChg = [sweptLayout.usedDims[0] - opts.tileSpacing, 0];
				newDims[0] += -sweptLayout.usedDims[0] + opts.tileSpacing;
			} else {
				xyChg = [0, sweptLayout.usedDims[1] - opts.tileSpacing];
				newDims[1] += -sweptLayout.usedDims[1] + opts.tileSpacing;
			}
			tempTree = new LayoutNode(new TolNode('SWEEP_REM_' + node.tolNode.name), nonLeaves);
			if (nonLeaves.length > 1){
				nonLeavesLayout = rectLayoutFn(tempTree, [0,0], newDims, false, opts, {subLayoutFn:sweepLayoutFn});
			} else {
				//get leftover swept-layout-area to propagate
				let leftoverArea : SepSweptArea;
				if (sweptLeft){
					leftoverArea = new SepSweptArea( //pos is relative to the non-leaves-area
						[-sweptLayout.usedDims[0]+opts.tileSpacing, sweptLayout.usedDims[1]-opts.tileSpacing],
						[sweptLayout.usedDims[0]-opts.tileSpacing*2,
							newDims[1]-sweptLayout.usedDims[1]-opts.tileSpacing],
						sweptLeft
					);
				} else {
					leftoverArea = new SepSweptArea(
						[sweptLayout.usedDims[0]-opts.tileSpacing, -sweptLayout.usedDims[1]+opts.tileSpacing],
						[newDims[0]-sweptLayout.usedDims[0]-opts.tileSpacing,
							sweptLayout.usedDims[1]-opts.tileSpacing*2],
						sweptLeft
					);
				}
				leftoverArea.dims[0] = Math.max(0, leftoverArea.dims[0]);
				leftoverArea.dims[1] = Math.max(0, leftoverArea.dims[1]);
				//generate layout
				nonLeavesLayout = rectLayoutFn(tempTree, [0,0], newDims, false, opts,
					{subLayoutFn: (n,p,d,h,o) => sweepLayoutFn(n,p,d,h,o,{sepSweptArea:leftoverArea})});
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
		let newNode = new LayoutNode(node.tolNode, layoutsInOldOrder, pos, dims, {
			showHeader,
			usedDims: [
				usingParentArea ? nonLeavesLayout.dims[0] : (sweptLeft ?
					sweptLayout.dims[0] + nonLeavesLayout.dims[0] - opts.tileSpacing :
					Math.max(sweptLayout.dims[0], nonLeavesLayout.dims[0])),
				usingParentArea ? nonLeavesLayout.dims[1] + headerSz : (sweptLeft ?
					Math.max(sweptLayout.dims[1], nonLeavesLayout.dims[1]) + headerSz :
					sweptLayout.dims[1] + nonLeavesLayout.dims[1] - opts.tileSpacing + headerSz),
			],
			empSpc: sweptLayout.empSpc + nonLeavesLayout.empSpc,
			sepSweptArea: (usingParentArea && parentArea) ? parentArea : null,
		});
		layoutsInOldOrder.forEach(n => n.parent = newNode);
		return newNode;
	}
}

//clips values in array to within [min,max], and redistributes to compensate, returning null if unable
function limitVals(arr: number[], min: number, max: number): number[]|null {
	let vals = [...arr];
	let clipped = arrayOf(false, vals.length);
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
function arrayOf(val: any, len: number){ //returns an array of 'len' 'val's
	return Array(len).fill(val);
}
function seq(len: number){ //returns [0, ..., len]
	return [...Array(len).keys()];
}
