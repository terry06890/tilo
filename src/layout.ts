export {staticSqrLayout, staticRectLayout, sweepToSideLayout, layoutInfoHooks};
export type {TolNode, TreeNode, LayoutNode};

let TILE_SPACING = 5;
let HEADER_SZ = 20;
let MIN_TILE_SZ = 50;
let MAX_TILE_SZ = 200;
let RECT_MODE = 'auto'; //'horz', 'vert', 'linear', 'auto'
let SWEEP_MODE = 'left'; //'left', 'top', 'shorter', 'auto'
let ALLOW_SWEEP_TO_PARENT = true;
let RECT_SPC_SHIFTING = true;

interface TolNode {
	name: string;
	children: TolNode[];
}
interface TreeNode {
	tolNode: TolNode;
	children: TreeNode[];
	x: number;
	y: number;
	w: number;
	h: number;
	headerSz: number;
	sideArea: SideArea | null;
	tileCount: number;
}
interface LayoutNode {
	name: string;
	x: number;
	y: number;
	w: number;
	h: number;
	headerSz: number;
	children: LayoutNode[];
	contentW: number;
	contentH: number;
	empSpc: number;
	sideArea: SideArea | null;
}
interface SideArea {
	x: number;
	y: number;
	w: number;
	h: number;
	sweptLeft: boolean;
	extraSz: number;
}
interface LeftoverArea {
	parentX: number;
	parentY: number;
	w: number;
	h: number;
	sweptLeft: boolean;
}

const layoutInfoHooks = { //made common-across-layout-types for layout inter-usability
	initLayoutInfo(tree: TreeNode){
		if (tree.children.length > 0){
			tree.children.forEach((n: TreeNode) => this.initLayoutInfo(n));
		}
		this.updateLayoutInfo(tree);
	},
	updateLayoutInfoOnExpand(nodeList: TreeNode[]){
		//given list of tree-nodes from expanded_child-to-parent, update layout-info
		nodeList[0].children.forEach(this.updateLayoutInfo);
		for (let node of nodeList){
			this.updateLayoutInfo(node);
		}
	},
	updateLayoutInfoOnCollapse(nodeList: TreeNode[]){
		//given list of tree-nodes from child_to_collapse-to-parent, update layout-info
		for (let node of nodeList){
			this.updateLayoutInfo(node);
		}
	},
	updateLayoutInfo(tree: TreeNode){
		if (tree.children.length == 0){
			tree.tileCount = 1;
		} else {
			tree.tileCount = tree.children.map(e => e.tileCount).reduce((x,y) => x+y);
		}
	}
}

//lays out nodes as squares in a rectangle, with spacing
function staticSqrLayout(node: TreeNode, x: number, y: number, w: number, h: number, hideHeader: boolean)
	: LayoutNode|null {
	//get number-of-columns with lowest leftover empty space
	let headerSz = (hideHeader ? 0 : HEADER_SZ);
	let availW = w - TILE_SPACING, availH = h - headerSz - TILE_SPACING;
	if (availW*availH <= 0)
		return null;
	let numChildren = node.children.length, ar = availW/availH;
	let lowestEmp = Number.POSITIVE_INFINITY, numCols = 0, numRows = 0, tileSize = 0;
	for (let nc = 1; nc <= numChildren; nc++){
		let nr = Math.ceil(numChildren/nc);
		let ar2 = nc/nr;
		let frac = ar > ar2 ? ar2/ar : ar/ar2;
		let tileSz = ar > ar2 ? availH/nr-TILE_SPACING : availW/nc-TILE_SPACING;
		if (tileSz < MIN_TILE_SZ)
			continue;
		else if (tileSz > MAX_TILE_SZ)
			tileSz = MAX_TILE_SZ;
		let empSpc = (1-frac)*availW*availH + (nc*nr-numChildren)*(tileSz - TILE_SPACING)**2;
		if (empSpc < lowestEmp){
			lowestEmp = empSpc;
			numCols = nc;
			numRows = nr;
			tileSize = tileSz;
		}
	}
	if (lowestEmp == Number.POSITIVE_INFINITY)
		return null;
	let childLayouts = arrayOf(0, numChildren);
	for (let i = 0; i < numChildren; i++){
		let childX = TILE_SPACING + (i % numCols)*(tileSize + TILE_SPACING);
		let childY = TILE_SPACING + headerSz + Math.floor(i / numCols)*(tileSize + TILE_SPACING);
		if (node.children[i].children.length == 0){
			childLayouts[i] = {
				x: childX, y: childY, w: tileSize, h: tileSize, headerSz: 0,
				children: [],
				contentW: tileSize, contentH: tileSize, empSpc: 0,
			}
		} else {
			childLayouts[i] = staticSqrLayout(node.children[i], childX, childY, tileSize, tileSize, false);
			if (childLayouts[i] == null)
				return null;
			lowestEmp += childLayouts[i].empSpc;
		}
	}
	return {
		name: node.tolNode.name,
		x: x, y: y, w: w, h: h, headerSz: headerSz,
		children: childLayouts,
		contentW: numCols * (tileSize + TILE_SPACING) + TILE_SPACING,
		contentH: numRows * (tileSize + TILE_SPACING) + TILE_SPACING + headerSz,
		empSpc: lowestEmp,
		sideArea: null,
	};
}
//lays out nodes as rectangles organised into rows, partially using other layouts for children
function staticRectLayout(node: TreeNode, x: number, y: number, w: number, h: number, hideHeader: boolean,
	subLayoutGen
		:(node:TreeNode, x:number, y:number, w:number, h:number, hideHeader:boolean) => LayoutNode|null
		= staticRectLayout)
	: LayoutNode|null {
	if (node.children.every(n => n.children.length == 0))
		return staticSqrLayout(node, x, y, w, h, hideHeader);
	//find grid-arrangement with lowest leftover empty space
	let headerSz = (hideHeader ? 0 : HEADER_SZ);
	let availW = w - TILE_SPACING, availH = h - TILE_SPACING - headerSz;
	let numChildren = node.children.length;
	let rowBrks: number[]|null = null; //will holds node indices at which each row starts
	let lowestEmp = Number.POSITIVE_INFINITY, rowBreaks = null, childLayouts = null;
	rowBrksLoop:
	while (true){
		//update rowBrks or exit loop
		if (rowBrks == null){
			if (RECT_MODE == 'vert'){
				rowBrks = seq(numChildren);
			} else {
				rowBrks = [0];
			}
		} else {
			if (RECT_MODE == 'horz' || RECT_MODE == 'vert'){
				break rowBrksLoop;
			} else if (RECT_MODE == 'linear'){
				if (rowBrks.length == 1 && numChildren > 1)
					rowBrks = seq(numChildren);
				else
					break rowBrksLoop;
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
		//create list-of-lists representing each row's cells' tileCounts
		let rowsOfCnts: number[][] = arrayOf([], rowBrks.length);
		for (let r = 0; r < rowBrks.length; r++){
			let numNodes = (r == rowBrks.length-1) ? numChildren-rowBrks[r] : rowBrks[r+1]-rowBrks[r];
			let rowNodeIdxs = seq(numNodes).map(i => i+rowBrks![r]);
			rowsOfCnts[r] = rowNodeIdxs.map(idx => node.children[idx].tileCount);
		}
		//get cell dims
		let totalTileCount = node.children.map(n => n.tileCount).reduce((x,y) => x+y);
		let cellHs = rowsOfCnts.map(row => row.reduce((x, y) => x+y) / totalTileCount * availH);
		let cellWs = arrayOf(0, numChildren);
		for (let r = 0; r < rowsOfCnts.length; r++){
			let rowCount = rowsOfCnts[r].reduce((x,y) => x+y);
			for (let c = 0; c < rowsOfCnts[r].length; c++){
				cellWs[rowBrks[r]+c] = rowsOfCnts[r][c] / rowCount * availW;
			}
		}
		//impose min-tile-size
		cellHs = limitVals(cellHs, MIN_TILE_SZ, Number.POSITIVE_INFINITY)!;
		if (cellHs == null)
			continue rowBrksLoop;
		for (let r = 0; r < rowsOfCnts.length; r++){
			let temp = limitVals(cellWs.slice(rowBrks[r], rowBrks[r] + rowsOfCnts[r].length),
				MIN_TILE_SZ, Number.POSITIVE_INFINITY);
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
		let childLyts = arrayOf(0, numChildren);
		let empVTotal = 0, empSpc = 0;
		for (let r = 0; r < rowBrks.length; r++){
			let empHorzTotal = 0;
			for (let c = 0; c < rowsOfCnts[r].length; c++){
				let nodeIdx = rowBrks[r]+c;
				let child = node.children[nodeIdx];
				let childX = cellXs[nodeIdx] + TILE_SPACING, childY = cellYs[r] + TILE_SPACING + headerSz,
					childW = cellWs[nodeIdx] - TILE_SPACING, childH = cellHs[r] - TILE_SPACING;
				if (child.children.length == 0){
					let contentSz = Math.min(childW, childH);
					childLyts[nodeIdx] = {
						x: childX, y: childY, w: childW, h: childH, headerSz: 0,
						children: [],
						contentW: contentSz, contentH: contentSz, empSpc: childW*childH - contentSz**2,
					};
				} else if (child.children.every(n => n.children.length == 0)){
					childLyts[nodeIdx] = staticSqrLayout(child, childX, childY, childW, childH, false);
				} else {
					childLyts[nodeIdx] = subLayoutGen(child, childX, childY, childW, childH, false);
				}
				if (childLyts[nodeIdx] == null)
					continue rowBrksLoop;
				//handle horizontal empty-space-shifting
				if (RECT_SPC_SHIFTING){
					let empHorz = childLyts[nodeIdx].w - childLyts[nodeIdx].contentW;
					childLyts[nodeIdx].w -= empHorz;
					childLyts[nodeIdx].empSpc -= empHorz * childLyts[nodeIdx].h;
					if (c < rowsOfCnts[r].length-1){
						cellXs[nodeIdx+1] -= empHorz;
						cellWs[nodeIdx+1] += empHorz;
					} else {
						empHorzTotal = empHorz;
					}
				}
			}
			//handle vertical empty-space-shifting
			if (RECT_SPC_SHIFTING){
				let nodeIdxs = seq(rowsOfCnts[r].length).map(i => rowBrks![r]+i);
				let empVerts = nodeIdxs.map(idx => childLyts[idx].h - childLyts[idx].contentH);
				let minEmpVert = Math.min(...empVerts);
				nodeIdxs.forEach(idx => {
					childLyts[idx].h -= minEmpVert;
					childLyts[idx].empSpc -= minEmpVert * childLyts[idx].w;
				});
				if (r < rowBrks.length-1){
					cellYs[r+1] -= minEmpVert;
					cellHs[r+1] += minEmpVert;
				} else {
					empVTotal = minEmpVert;
				}
			}
			//other updates
			empSpc += empHorzTotal * childLyts[rowBrks[r]].h;
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
	childLayouts.filter(l => l.children.length == 0).forEach(l => {l.w = l.contentW; l.h = l.contentH;});
	//determine layout
	return {
		name: node.tolNode.name,
		x: x, y: y, w: w, h: h, headerSz: headerSz,
		children: childLayouts,
		contentW: w, //trying to shrink this causes problems with swept-to-parent-area div-alignment
		contentH: h,
		empSpc: lowestEmp,
		sideArea: null,
	};
}
//lays out nodes by pushing leaves to one side, partially using other layouts for children
function sweepToSideLayout(node: TreeNode, x: number, y: number, w: number, h: number, hideHeader: boolean,
	parentArea: LeftoverArea|null = null): LayoutNode|null {
	//separate leaf and non-leaf nodes
	let leaves: TreeNode[] = [], nonLeaves: TreeNode[] = [];
	node.children.forEach(n => (n.children.length == 0 ? leaves : nonLeaves).push(n));
	//determine layout
	let tempTree: TreeNode;
	if (nonLeaves.length == 0){ //if all leaves, use squares-layout
		return staticSqrLayout(node, x, y, w, h, hideHeader);
	} else if (leaves.length == 0){
		tempTree = {tolNode: {name: 'SWEEP_REM_' + node.tolNode.name, children: []}, children: nonLeaves,
			x:0, y:0, w:0, h:0, headerSz:0, sideArea:null, tileCount:0};
		return staticRectLayout(tempTree, x, y, w, h, hideHeader, sweepToSideLayout);
	} else {
		let ratio = leaves.length / (leaves.length + nonLeaves.map(e => e.tileCount).reduce((x,y) => x+y));
		let headerSz = (hideHeader ? 0 : HEADER_SZ);
		let sweptLayout = null, nonLeavesLayout = null, sweptLeft = false, leftOverArea: LeftoverArea;
		//get swept-area layout
		let usingParentArea = false;
		if (ALLOW_SWEEP_TO_PARENT && parentArea != null){
			tempTree = {tolNode: {name: 'SWEEP_' + node.tolNode.name, children: []}, children: leaves,
				x:0, y:0, w:0, h:0, headerSz:0, sideArea:null, tileCount:0};
			sweptLeft = parentArea.sweptLeft;
			sweptLayout = staticSqrLayout(tempTree, 0, 0, parentArea.w, parentArea.h, sweptLeft);
			if (sweptLayout != null){
				let area = {x: x, y: y+headerSz, w: w, h: h-headerSz};
				if (!sweptLeft){ //no remaining-area header if swept-upward
					area.y = y; area.h = h;
				}
				//get remaining-area layout
				tempTree = {tolNode: {name: 'SWEEP_REM_' + node.tolNode.name, children: []}, children: nonLeaves,
					x:0, y:0, w:0, h:0, headerSz:0, sideArea:null, tileCount:0};
				if (nonLeaves.length > 1){
					nonLeavesLayout = staticRectLayout(tempTree, 0, 0, area.w, area.h, true, sweepToSideLayout);
				} else {
					//get leftover swept-layout-area to propagate
					let leftOverWidth = parentArea.w - sweptLayout.contentW;
					let leftOverHeight = parentArea.h - sweptLayout.contentH;
					leftOverArea = sweptLeft ?
						{...parentArea, parentY:parentArea.parentY+sweptLayout.contentH-TILE_SPACING-headerSz,
							h:leftOverHeight-TILE_SPACING} :
						{...parentArea,
							parentX:parentArea.parentX+sweptLayout.contentW-TILE_SPACING,
							parentY:parentArea.parentY + headerSz,
							w:leftOverWidth-TILE_SPACING, h:parentArea.h - headerSz};
					//call genLayout
					nonLeavesLayout = staticRectLayout(
						tempTree, 0, 0, area.w, area.h, true,
						(n,x,y,w,h,hh) => sweepToSideLayout(n,x,y,w,h,hh,leftOverArea));
				}
				if (nonLeavesLayout != null){
					nonLeavesLayout.children.forEach(layout => {layout.y += (sweptLeft ? headerSz : 0)});
					usingParentArea = true;
				}
			}
		}
		if (!usingParentArea){
			let area = {x: x, y: y+headerSz, w: w, h: h-headerSz};
			tempTree = {tolNode: {name: 'SWEEP_' + node.tolNode.name, children: []}, children: leaves,
				x:0, y:0, w:0, h:0, headerSz:0, sideArea:null, tileCount:0};
			let xyChg: [number, number];
			//get swept-area layout
			let leftLayout = null, topLayout = null;
			let documentAR = document.documentElement.clientWidth / document.documentElement.clientHeight;
			if (SWEEP_MODE == 'left' || (SWEEP_MODE == 'shorter' && documentAR >= 1) || SWEEP_MODE == 'auto'){
				leftLayout = staticSqrLayout(tempTree, 0, 0,
					Math.max(area.w*ratio, MIN_TILE_SZ+TILE_SPACING*2), area.h, true);
			} else if (SWEEP_MODE == 'top' || (SWEEP_MODE == 'shorter' && documentAR < 1) || SWEEP_MODE == 'auto'){
				topLayout = staticSqrLayout(tempTree, 0, 0,
					area.w, Math.max(area.h*ratio, MIN_TILE_SZ+TILE_SPACING*2), true);
			}
			if (SWEEP_MODE == 'auto'){
				sweptLayout =
					(leftLayout && topLayout && ((leftLayout.empSpc < topLayout.empSpc) ? leftLayout : topLayout)) ||
					leftLayout || topLayout;
			} else {
				sweptLayout = leftLayout || topLayout;
			}
			sweptLeft = (sweptLayout == leftLayout);
			if (sweptLayout == null)
				return null;
			sweptLayout.children.forEach(layout => {layout.y += headerSz});
			//get remaining-area layout
			if (sweptLeft){
				xyChg = [sweptLayout.contentW - TILE_SPACING, 0];
				area.w += -sweptLayout.contentW + TILE_SPACING;
			} else {
				xyChg = [0, sweptLayout.contentH - TILE_SPACING];
				area.h += -sweptLayout.contentH + TILE_SPACING;
			}
			tempTree = {tolNode: {name: 'SWEEP_REM_' + node.tolNode.name, children: []}, children: nonLeaves,
				x:0, y:0, w:0, h:0, headerSz:0, sideArea:null, tileCount:0};
			if (nonLeaves.length > 1){
				nonLeavesLayout = staticRectLayout(tempTree, 0, 0, area.w, area.h, true, sweepToSideLayout);
			} else {
				//get leftover swept-layout-area to propagate
				if (sweptLeft){
					leftOverArea = { //parentX and parentY are relative to the non-leaves-area
						parentX: -sweptLayout.contentW + TILE_SPACING, parentY: sweptLayout.contentH - TILE_SPACING,
						w: sweptLayout.contentW - TILE_SPACING*2, h: area.h-sweptLayout.contentH - TILE_SPACING,
						sweptLeft
					};
				} else {
					leftOverArea = {
						parentX: sweptLayout.contentW - TILE_SPACING, parentY: -sweptLayout.contentH + TILE_SPACING,
						w: area.w-sweptLayout.contentW - TILE_SPACING, h: sweptLayout.contentH - TILE_SPACING*2,
						sweptLeft
					};
				}
				leftOverArea.w = Math.max(0, leftOverArea.w);
				leftOverArea.h = Math.max(0, leftOverArea.h);
				//call genLayout
				nonLeavesLayout = staticRectLayout(
					tempTree, 0, 0, area.w, area.h, true,
					(n,x,y,w,h,hh) => sweepToSideLayout(n,x,y,w,h,hh,leftOverArea));
			}
			if (nonLeavesLayout == null)
				return null;
			nonLeavesLayout.children.forEach(layout => {layout.x += xyChg[0]; layout.y += xyChg[1] + headerSz;});
		}
		if (sweptLayout == null || nonLeavesLayout == null) //hint for tsc
			return null;
		//return combined layouts
		let children = leaves.concat(nonLeaves);
		let layouts = sweptLayout.children.concat(nonLeavesLayout.children);
		let layoutsInOldOrder = seq(node.children.length)
			.map(i => children.findIndex(n => n == node.children[i]))
			.map(i => layouts[i]);
		return {
			name: node.tolNode.name,
			x: x, y: y, w: w, h: h, headerSz: headerSz,
			children: layoutsInOldOrder,
			contentW: usingParentArea ? nonLeavesLayout.contentW : (sweptLeft ?
				sweptLayout.contentW + nonLeavesLayout.contentW - TILE_SPACING :
				Math.max(sweptLayout.contentW, nonLeavesLayout.contentW)),
			contentH: usingParentArea ? nonLeavesLayout.contentH + headerSz : (sweptLeft ?
				Math.max(sweptLayout.contentH, nonLeavesLayout.contentH) + headerSz :
				sweptLayout.contentH + nonLeavesLayout.contentH - TILE_SPACING + headerSz),
			empSpc: sweptLayout.empSpc + nonLeavesLayout.empSpc,
			sideArea: usingParentArea && parentArea != null ? {
				x: parentArea.parentX, y: parentArea.parentY,
				w: parentArea.w, h: parentArea.h,
				sweptLeft: sweptLeft, extraSz: TILE_SPACING+1,
			}: null,
		};
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