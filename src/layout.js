export {staticSqrLayout, staticRectLayout, sweepToSideLayout};

const TILE_SPACING = 5;
const HEADER_SZ = 20;
const MIN_TILE_SZ = 50;
const MAX_TILE_SZ = 200;

const staticSqrLayout = { //lays out nodes as squares in a rectangle, with spacing
	genLayout(node, x, y, w, h, hideHeader){
		//get number-of-columns with lowest leftover empty space
		let headerSz = (hideHeader ? 0 : HEADER_SZ);
		let availW = w - TILE_SPACING, availH = h - headerSz - TILE_SPACING;
		let numChildren = node.children.length, ar = availW/availH;
		let lowestEmp = Number.POSITIVE_INFINITY, numCols, numRows, tileSize;
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
		let childLayouts = Array(numChildren).fill();
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
				childLayouts[i] = this.genLayout(node.children[i], childX, childY, tileSize, tileSize, false);
				if (childLayouts[i] == null)
					return null;
				lowestEmp += childLayouts[i].empSpc;
			}
		}
		return {
			x: x, y: y, w: w, h: h, headerSz: headerSz,
			children: childLayouts,
			contentW: numCols * (tileSize + TILE_SPACING) + TILE_SPACING,
			contentH: numRows * (tileSize + TILE_SPACING) + TILE_SPACING + headerSz,
			empSpc: lowestEmp,
		}
	},
	initLayoutInfo(tree){
		return;
	},
	updateLayoutInfoOnExpand(nodeList){
		return;
	},
	updateLayoutInfoOnCollapse(nodeList){
		return;
	}
};
const staticRectLayout = {
	genLayout(node, x, y, w, h, hideHeader, subLayoutGen = staticRectLayout.genLayout){
		if (node.children.every(n => n.children.length == 0))
			return staticSqrLayout.genLayout(node, x, y, w, h, hideHeader);
		//find grid-arrangement with lowest leftover empty space
		let headerSz = (hideHeader ? 0 : HEADER_SZ);
		let availW = w - TILE_SPACING, availH = h - TILE_SPACING - headerSz;
		let numChildren = node.children.length;
		let rowBrks = null; //will holds node indices at which each row starts
		let lowestEmp = Number.POSITIVE_INFINITY, rowBreaks, rowsOfCounts, childLayouts;
		rowBrksLoop:
		while (true){
			//update rowBrks or exit loop
			if (rowBrks == null){
				rowBrks = [0];
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
							rowBrks = Array.from({length: rowBrks.length+1}, (x,i) => i);
						} else {
							break rowBrksLoop;
						}
						break;
					}
				}
			}
			//create list-of-lists representing each row's cells' tileCounts
			let rowsOfCnts = Array(rowBrks.length).fill();
			for (let r = 0; r < rowBrks.length; r++){
				let numNodes = (r == rowBrks.length-1) ? numChildren-rowBrks[r] : rowBrks[r+1]-rowBrks[r];
				let rowNodeIdxs = Array.from({length: numNodes}, (x,i) => i+rowBrks[r]);
				rowsOfCnts[r] = rowNodeIdxs.map(idx => node.children[idx].tileCount);
			}
			//get cell dims
			let totalTileCount = node.children.map(n => n.tileCount).reduce((x,y) => x+y);
			let cellHs = rowsOfCnts.map(row => row.reduce((x, y) => x+y) / totalTileCount * availH);
			let cellWs = Array(numChildren).fill();
			for (let r = 0; r < rowsOfCnts.length; r++){
				let rowCount = rowsOfCnts[r].reduce((x,y) => x+y);
				for (let c = 0; c < rowsOfCnts[r].length; c++){
					cellWs[rowBrks[r]+c] = rowsOfCnts[r][c] / rowCount * availW;
				}
			}
			//impose min-tile-size
			cellHs = limitVals(cellHs, MIN_TILE_SZ, Number.POSITIVE_INFINITY);
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
			let cellXs = Array(cellWs.length).fill(0);
			for (let r = 0; r < rowBrks.length; r++){
				for (let c = 1; c < rowsOfCnts[r].length; c++){
					let nodeIdx = rowBrks[r]+c;
					cellXs[nodeIdx] = cellXs[nodeIdx-1] + cellWs[nodeIdx-1];
				}
			}
			let cellYs = Array(cellHs.length).fill(0);
			for (let r = 1; r < rowBrks.length; r++){
				cellYs[r] = cellYs[r-1] + cellHs[r-1];
			}
			//get child layouts and empty-space
			let childLyts = Array(numChildren).fill(), empSpc = 0;
			for (let r = 0; r < rowBrks.length; r++){
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
						childLyts[nodeIdx] = staticSqrLayout.genLayout(child, childX, childY, childW, childH, false);
					} else {
						childLyts[nodeIdx] = subLayoutGen(child, childX, childY, childW, childH, false);
					}
					if (childLyts[nodeIdx] == null)
						continue rowBrksLoop;
					empSpc += childLyts[nodeIdx].empSpc;
				}
			}
			//check with best-so-far
			if (empSpc < lowestEmp){
				lowestEmp = empSpc;
				rowBreaks = [...rowBrks];
				rowsOfCounts = rowsOfCnts;
				childLayouts = childLyts;
			}
		}
		if (rowBreaks == null)
			return null;
		//for each row, shift empty right-space to rightmost cell
		let minEmpHorzTotal = Number.POSITIVE_INFINITY;
		for (let r = 0; r < rowBreaks.length; r++){
			let empHorzTotal = 0, leftShiftTotal = 0;
			for (let c = 0; c < rowsOfCounts[r].length - 1; c++){
				let nodeIdx = rowBreaks[r] + c;
				let empHorz = childLayouts[nodeIdx].w - childLayouts[nodeIdx].contentW;
				childLayouts[nodeIdx].w -= empHorz;
				empHorzTotal += empHorz;
				childLayouts[nodeIdx+1].x -= empHorzTotal;
			}
			childLayouts[rowBreaks[r] + rowsOfCounts[r].length - 1].w += empHorzTotal;
			if (empHorzTotal < minEmpHorzTotal)
				minEmpHorzTotal = empHorzTotal;
		}
		//shift empty bottom-space to bottom-most row
		let empVertTotal = 0;
		for (let r = 0; r < rowBreaks.length - 1; r++){
			let nodeIdxs = Array.from({length: rowsOfCounts[r].length}, (x,i) => rowBreaks[r] + i);
			nodeIdxs.forEach(idx => childLayouts[idx].y -= empVertTotal);
			let empVerts = nodeIdxs.map(idx => childLayouts[idx].h - childLayouts[idx].contentH);
			let minEmpVert = Math.min(...empVerts);
			nodeIdxs.forEach(idx => childLayouts[idx].h -= minEmpVert);
			empVertTotal += minEmpVert;
		}
		let lastRowIdx = rowBreaks.length-1;
		let lastNodeIdxs = Array.from({length: rowsOfCounts[lastRowIdx].length}, (x,i) => rowBreaks[lastRowIdx] + i);
		lastNodeIdxs.forEach(idx => childLayouts[idx].y -= empVertTotal);
		lastNodeIdxs.map(idx => childLayouts[idx].h += empVertTotal);
		//make no-child tiles have width/height fitting their content
		childLayouts.forEach(lyt => {
			if (lyt.children.length == 0){lyt.w = lyt.contentW; lyt.h = lyt.contentH;}
		});
		//determine layout
		return {
			x: x, y: y, w: w, h: h, headerSz: headerSz,
			children: childLayouts,
			contentW: w - minEmpHorzTotal,
			contentH: h - empVertTotal,
			empSpc: lowestEmp,
		}
	},
	initLayoutInfo(tree){
		if (tree.children.length > 0){
			tree.children.forEach(e => this.initLayoutInfo(e));
		}
		this.updateLayoutInfo(tree);
	},
	updateLayoutInfoOnExpand(nodeList){ //given list of tree-nodes from expanded_child-to-parent, update layout-info
		nodeList[0].children.forEach(this.updateLayoutInfo);
		for (let node of nodeList){
			this.updateLayoutInfo(node);
		}
	},
	updateLayoutInfoOnCollapse(nodeList){ //given list of tree-nodes from child_to_collapse-to-parent, update layout-info
		for (let node of nodeList){
			this.updateLayoutInfo(node);
		}
	},
	updateLayoutInfo(tree){
		if (tree.children.length == 0){
			tree.tileCount = 1;
		} else {
			tree.tileCount = tree.children.map(e => e.tileCount).reduce((x,y) => x+y);
		}
	}
};
const sweepToSideLayout = {
	genLayout(node, x, y, w, h, hideHeader, parentArea = null){
		let SWEEP_LEFT_ONLY = true, ALLOW_PARENT_AREA = true;
		//separate leaf and non-leaf nodes
		let leaves = [], nonLeaves = [];
		node.children.forEach(n => (n.children.length == 0 ? leaves : nonLeaves).push(n));
		//determine layout
		let tempTree;
		if (nonLeaves.length == 0){ //if all leaves, use squares-layout
			return staticSqrLayout.genLayout(node, x, y, w, h, hideHeader);
		} else if (leaves.length == 0){
			tempTree = {tolNode: null, children: nonLeaves};
			return staticRectLayout.genLayout(tempTree, x, y, w, h, hideHeader);
		} else {
			let ratio = leaves.length / (leaves.length + nonLeaves.map(e => e.tileCount).reduce((x,y) => x+y));
			let headerSz = (hideHeader ? 0 : HEADER_SZ);
			let area = {x: x, y: y+headerSz, w: w, h: h-headerSz};
			let sweptLayout, nonLeavesLayout, sweptLeft = false;
			//get swept-area layout
			let usingParentArea = false;
			if (ALLOW_PARENT_AREA && parentArea != null){
				tempTree = {tolNode: null, children: leaves};
				sweptLayout = staticSqrLayout.genLayout(tempTree, 0, 0, parentArea.w, parentArea.h, true);
				if (sweptLayout != null){
					sweptLayout.children.forEach(layout => {
						layout.x += -x+parentArea.x;
						layout.y += -y+parentArea.y;
					});
					//get remaining-area layout
					tempTree = {tolNode: null, children: nonLeaves};
					if (nonLeaves.length > 1){
						nonLeavesLayout = staticRectLayout.genLayout(
							tempTree, 0, 0, area.w, area.h, true, sweepToSideLayout.genLayout);
					} else {
						//get leftover swept-layout-area to propagate
						let leftOverWidth = parentArea.w - sweptLayout.contentW;
						let leftOverHeight = parentArea.h - sweptLayout.contentH;
						let leftOverArea = (leftOverWidth > leftOverHeight) ?
							{x: parentArea.x+sweptLayout.contentW, y: parentArea.y, w: leftOverWidth, h: parentArea.h} :
							{x: parentArea.x, y: parentArea.y+sweptLayout.contentH, w: parentArea.w, h: leftOverHeight};
						leftOverArea.x += -TILE_SPACING;
						leftOverArea.y += -headerSz - TILE_SPACING*2;
						//call genLayout
						nonLeavesLayout = staticRectLayout.genLayout(
							tempTree, 0, 0, area.w, area.h, true,
							(n,x,y,w,h,hh) => sweepToSideLayout.genLayout(n,x,y,w,h,hh,leftOverArea));
					}
					if (nonLeavesLayout != null){
						nonLeavesLayout.children.forEach(layout => {layout.y += headerSz});
						usingParentArea = true;
					}
				}
			}
			if (!usingParentArea){
				tempTree = {tolNode: null, children: leaves};
				let xyChg, leftOverArea;
				if (SWEEP_LEFT_ONLY){
					sweptLayout = staticSqrLayout.genLayout(tempTree, 0, 0,
						Math.max(area.w*ratio, MIN_TILE_SZ+TILE_SPACING*2), area.h, true);
					sweptLeft = true;
				} else {
					let leftLayout = staticSqrLayout.genLayout(tempTree, 0, 0,
						Math.max(area.w*ratio, MIN_TILE_SZ+TILE_SPACING*2), area.h, true);
					let topLayout = staticSqrLayout.genLayout(tempTree, 0, 0,
						area.w, Math.max(area.h*ratio, MIN_TILE_SZ+TILE_SPACING*2), true);
					sweptLayout =
						(leftLayout && topLayout && (leftLayout.empSpc < topLayout.empSpc) ? leftLayout : topLayout) ||
						leftLayout || topLayout;
					sweptLeft = (sweptLayout == leftLayout);
				}
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
				tempTree = {tolNode: null, children: nonLeaves};
				if (nonLeaves.length > 1){
					nonLeavesLayout = staticRectLayout.genLayout(
						tempTree, 0, 0, area.w, area.h, true, sweepToSideLayout.genLayout);
				} else {
					//get leftover swept-layout-area to propagate
					if (sweptLeft){
						leftOverArea = { //x and y are relative to a non-leaf child node
							x: -sweptLayout.contentW + TILE_SPACING, y: sweptLayout.contentH - TILE_SPACING,
							w: sweptLayout.contentW, h: area.h-sweptLayout.contentH
						};
					} else {
						leftOverArea = {
							x: sweptLayout.contentW - TILE_SPACING, y: -sweptLayout.contentH + TILE_SPACING,
							w: area.w-sweptLayout.contentW, h: sweptLayout.contentH
						};
					}
					//call genLayout
					nonLeavesLayout = staticRectLayout.genLayout(
						tempTree, 0, 0, area.w, area.h, true,
						(n,x,y,w,h,hh) => sweepToSideLayout.genLayout(n,x,y,w,h,hh,leftOverArea));
				}
				if (nonLeavesLayout == null)
					return null;
				nonLeavesLayout.children.forEach(layout => {layout.x += xyChg[0]; layout.y += xyChg[1] + headerSz;});
			}
			//return combined layouts
			let children = leaves.concat(nonLeaves);
			let layouts = sweptLayout.children.concat(nonLeavesLayout.children);
			let layoutsInOldOrder = [...Array(node.children.length).keys()]
				.map(i => children.findIndex(n => n == node.children[i]))
				.map(i => layouts[i]);
			return {
				x: x, y: y, w: w, h: h, headerSz: headerSz,
				//children: [...sweptLayout.children, ...nonLeavesLayout.children],
				children: layoutsInOldOrder,
				contentW: sweptLeft ?
					sweptLayout.contentW + nonLeavesLayout.contentW - TILE_SPACING :
					Math.max(sweptLayout.contentW, nonLeavesLayout.contentW),
				contentH: sweptLeft ?
					Math.max(sweptLayout.contentH, nonLeavesLayout.contentH) :
					sweptLayout.contentH + nonLeavesLayout.contentH - TILE_SPACING,
				empSpc: sweptLayout.empSpc + nonLeavesLayout.empSpc,
			};
		}
	},
	initLayoutInfo(tree){
		if (tree.children.length > 0){
			tree.children.forEach(e => this.initLayoutInfo(e));
		}
		this.updateLayoutInfo(tree);
	},
	updateLayoutInfoOnExpand(nodeList){
		nodeList[0].children.forEach(this.updateLayoutInfo);
		for (let node of nodeList){
			this.updateLayoutInfo(node);
		}
	},
	updateLayoutInfoOnCollapse(nodeList){
		for (let node of nodeList){
			this.updateLayoutInfo(node);
		}
	},
	updateLayoutInfo(tree){
		if (tree.children.length == 0){
			tree.tileCount = 1;
		} else {
			tree.tileCount = tree.children.map(e => e.tileCount).reduce((x,y) => x+y);
		}
	}
};

//clips values in array to within [min,max], and redistributes to compensate, returning null if unable
function limitVals(arr, min, max){
	let vals = [...arr];
	let clipped = Array(vals.length).fill(false);
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
				(arr,n,i) => {if (n < max) arr.push(i); return arr;},
				[]);
		} else {
			indicesToUpdate = vals.reduce(
				(arr,n,i) => {if (n > min) arr.push(i); return arr;},
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
