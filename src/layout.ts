import {TolNode, LayoutNode, SepSweptArea} from './types';
export {genLayout, layoutInfoHooks};

type LayoutFn = (node: LayoutNode, x: number, y: number, w: number, h: number, hideHeader: boolean,
	options?: {subLayoutFn?: LayoutFn, sepSweptArea?: SepSweptArea|null}) => LayoutNode | null;

let TILE_SPACING = 5;
let HEADER_SZ = 20;
let MIN_TILE_SZ = 50;
let MAX_TILE_SZ = 200;
let RECT_MODE = 'auto'; //'horz', 'vert', 'linear', 'auto'
let SWEEP_MODE = 'left'; //'left', 'top', 'shorter', 'auto'
let ALLOW_SWEEP_TO_PARENT = true;
let RECT_SPC_SHIFTING = true;

const layoutInfoHooks = { //made common-across-layout-types for layout inter-usability
	initLayoutInfo(node: LayoutNode){
		if (node.children.length > 0){
			node.children.forEach((n: LayoutNode) => this.initLayoutInfo(n));
		}
		this.updateLayoutInfo(node);
	},
	updateLayoutInfoOnExpand(nodeList: LayoutNode[]){
		//given list of layout-nodes from expanded_child-to-parent, update layout-info
		nodeList[0].children.forEach(this.updateLayoutInfo);
		for (let node of nodeList){
			this.updateLayoutInfo(node);
		}
	},
	updateLayoutInfoOnCollapse(nodeList: LayoutNode[]){
		//given list of layout-nodes from child_to_collapse-to-parent, update layout-info
		for (let node of nodeList){
			this.updateLayoutInfo(node);
		}
	},
	updateLayoutInfo(node: LayoutNode){
		if (node.children.length == 0){
			node.tileCount = 1;
		} else {
			node.tileCount = node.children.map(n => n.tileCount).reduce((x,y) => x+y);
		}
	}
}

//lays out nodes as squares in a rectangle, with spacing
let sqrLayoutFn: LayoutFn = function (node, x, y, w, h, hideHeader){
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
		let child = node.children[i];
		let childX = TILE_SPACING + (i % numCols)*(tileSize + TILE_SPACING);
		let childY = TILE_SPACING + headerSz + Math.floor(i / numCols)*(tileSize + TILE_SPACING);
		if (child.children.length == 0){
			childLayouts[i] = new LayoutNode(child.tolNode, [], childX, childY, tileSize, tileSize,
				{headerSz: 0, contentW: tileSize, contentH: tileSize, empSpc: 0});
		} else {
			childLayouts[i] = sqrLayoutFn(child, childX, childY, tileSize, tileSize, false);
			if (childLayouts[i] == null)
				return null;
			lowestEmp += childLayouts[i].empSpc;
		}
	}
	return new LayoutNode(node.tolNode, childLayouts, x, y, w, h, {
		headerSz,
		contentW: numCols * (tileSize + TILE_SPACING) + TILE_SPACING,
		contentH: numRows * (tileSize + TILE_SPACING) + TILE_SPACING + headerSz,
		empSpc: lowestEmp,
	});
}
//lays out nodes as rectangles organised into rows, partially using other layouts for children
let rectLayoutFn: LayoutFn = function (node, x, y, w, h, hideHeader, options={subLayoutFn: rectLayoutFn}){
	if (node.children.every(n => n.children.length == 0))
		return sqrLayoutFn(node, x, y, w, h, hideHeader);
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
					childLyts[nodeIdx] = new LayoutNode(child.tolNode, [], childX, childY, childW, childH,
						{headerSz: 0, contentW: contentSz, contentH: contentSz, empSpc: childW*childH - contentSz**2});
				} else if (child.children.every(n => n.children.length == 0)){
					childLyts[nodeIdx] = sqrLayoutFn(child, childX, childY, childW, childH, false);
				} else {
					let layoutFn = (options && options.subLayoutFn) || rectLayoutFn;
					childLyts[nodeIdx] = layoutFn(child, childX, childY, childW, childH, false);
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
	return new LayoutNode(node.tolNode, childLayouts, x, y, w, h,
		{headerSz, contentW: w, contentH: h, empSpc: lowestEmp});
		//trying to shrink contentW and contentH causes problems with swept-to-parent-area div-alignment
}
//lays out nodes by pushing leaves to one side, partially using other layouts for children
let sweepLeavesLayoutFn: LayoutFn = function (node, x, y, w, h, hideHeader, options={sepSweptArea: null}){
	//separate leaf and non-leaf nodes
	let leaves: LayoutNode[] = [], nonLeaves: LayoutNode[] = [];
	node.children.forEach(n => (n.children.length == 0 ? leaves : nonLeaves).push(n));
	//determine layout
	let tempTree: LayoutNode;
	if (nonLeaves.length == 0){ //if all leaves, use squares-layout
		return sqrLayoutFn(node, x, y, w, h, hideHeader);
	} else if (leaves.length == 0){
		tempTree = new LayoutNode(new TolNode('SWEEP_REM_' + node.tolNode.name), nonLeaves);
		return rectLayoutFn(tempTree, x, y, w, h, hideHeader, {subLayoutFn: sweepLeavesLayoutFn});
	} else {
		let ratio = leaves.length / (leaves.length + nonLeaves.map(n => n.tileCount).reduce((x,y) => x+y));
		let headerSz = (hideHeader ? 0 : HEADER_SZ);
		let sweptLayout = null, nonLeavesLayout = null, sweptLeft = false;
		//get swept-area layout
		let parentArea = options && options.sepSweptArea, usingParentArea = false;
		if (ALLOW_SWEEP_TO_PARENT && parentArea){
			tempTree = new LayoutNode(new TolNode('SWEEP_' + node.tolNode.name), leaves);
			sweptLeft = parentArea.sweptLeft;
			sweptLayout = sqrLayoutFn(tempTree, 0, 0, parentArea.w, parentArea.h, sweptLeft);
			if (sweptLayout != null){
				let area = {x: x, y: y+headerSz, w: w, h: h-headerSz};
				if (!sweptLeft){ //no remaining-area header if swept-upward
					area.y = y; area.h = h;
				}
				//get remaining-area layout
				tempTree = new LayoutNode(new TolNode('SWEEP_REM_' + node.tolNode.name), nonLeaves);
				if (nonLeaves.length > 1){
					nonLeavesLayout = rectLayoutFn(tempTree, 0, 0, area.w, area.h, true,
						{subLayoutFn: sweepLeavesLayoutFn});
				} else {
					//get leftover swept-layout-area to propagate
					let leftOverWidth = parentArea.w - sweptLayout.contentW;
					let leftOverHeight = parentArea.h - sweptLayout.contentH;
					let leftoverArea = sweptLeft ?
						new SepSweptArea(
							parentArea.x, parentArea.y+sweptLayout.contentH-TILE_SPACING-headerSz,
							parentArea.w, leftOverHeight-TILE_SPACING, sweptLeft, TILE_SPACING) :
						new SepSweptArea(
							parentArea.x+sweptLayout.contentW-TILE_SPACING, parentArea.y + headerSz,
							leftOverWidth-TILE_SPACING, parentArea.h - headerSz, sweptLeft, TILE_SPACING);
					//call genLayout
					nonLeavesLayout = rectLayoutFn(
						tempTree, 0, 0, area.w, area.h, true,
						{subLayoutFn: (n,x,y,w,h,hh) => sweepLeavesLayoutFn(n,x,y,w,h,hh,{sepSweptArea:leftoverArea})});
				}
				if (nonLeavesLayout != null){
					nonLeavesLayout.children.forEach(layout => {layout.y += (sweptLeft ? headerSz : 0)});
					usingParentArea = true;
				}
			}
		}
		if (!usingParentArea){
			let area = {x: x, y: y+headerSz, w: w, h: h-headerSz};
			tempTree = new LayoutNode(new TolNode('SWEEP_' + node.tolNode.name), leaves);
			let xyChg: [number, number];
			//get swept-area layout
			let leftLayout = null, topLayout = null;
			let documentAR = document.documentElement.clientWidth / document.documentElement.clientHeight;
			if (SWEEP_MODE == 'left' || (SWEEP_MODE == 'shorter' && documentAR >= 1) || SWEEP_MODE == 'auto'){
				leftLayout = sqrLayoutFn(tempTree, 0, 0,
					Math.max(area.w*ratio, MIN_TILE_SZ+TILE_SPACING*2), area.h, true);
			} else if (SWEEP_MODE == 'top' || (SWEEP_MODE == 'shorter' && documentAR < 1) || SWEEP_MODE == 'auto'){
				topLayout = sqrLayoutFn(tempTree, 0, 0,
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
			tempTree = new LayoutNode(new TolNode('SWEEP_REM_' + node.tolNode.name), nonLeaves);
			if (nonLeaves.length > 1){
				nonLeavesLayout = rectLayoutFn(tempTree, 0, 0, area.w, area.h, true, {subLayoutFn: sweepLeavesLayoutFn});
			} else {
				//get leftover swept-layout-area to propagate
				let leftoverArea : SepSweptArea;
				if (sweptLeft){
					leftoverArea = new SepSweptArea( //x and y are relative to the non-leaves-area
						-sweptLayout.contentW + TILE_SPACING, sweptLayout.contentH - TILE_SPACING,
						sweptLayout.contentW - TILE_SPACING*2, area.h-sweptLayout.contentH - TILE_SPACING,
						sweptLeft, TILE_SPACING
					);
				} else {
					leftoverArea = new SepSweptArea(
						sweptLayout.contentW - TILE_SPACING, -sweptLayout.contentH + TILE_SPACING,
						area.w-sweptLayout.contentW - TILE_SPACING, sweptLayout.contentH - TILE_SPACING*2,
						sweptLeft, TILE_SPACING
					);
				}
				leftoverArea.w = Math.max(0, leftoverArea.w);
				leftoverArea.h = Math.max(0, leftoverArea.h);
				//call genLayout
				nonLeavesLayout = rectLayoutFn(
					tempTree, 0, 0, area.w, area.h, true,
					{subLayoutFn: (n,x,y,w,h,hh) => sweepLeavesLayoutFn(n,x,y,w,h,hh,{sepSweptArea:leftoverArea})});
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
		return new LayoutNode(node.tolNode, layoutsInOldOrder, x, y, w, h, {
			headerSz,
			contentW: usingParentArea ? nonLeavesLayout.contentW : (sweptLeft ?
				sweptLayout.contentW + nonLeavesLayout.contentW - TILE_SPACING :
				Math.max(sweptLayout.contentW, nonLeavesLayout.contentW)),
			contentH: usingParentArea ? nonLeavesLayout.contentH + headerSz : (sweptLeft ?
				Math.max(sweptLayout.contentH, nonLeavesLayout.contentH) + headerSz :
				sweptLayout.contentH + nonLeavesLayout.contentH - TILE_SPACING + headerSz),
			empSpc: sweptLayout.empSpc + nonLeavesLayout.empSpc,
			sepSweptArea: (usingParentArea && parentArea) ? parentArea : null,
		});
	}
}
//default layout function
let genLayout: LayoutFn = function (node, x, y, w, h, hideHeader){
	return sweepLeavesLayoutFn(node, x, y, w, h, hideHeader);
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
