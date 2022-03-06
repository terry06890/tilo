export {defaultLayout, initTree};

const DEFAULT_TILE_SPACING = 5;
const DEFAULT_HEADER_SZ = 20;

const staticSqrLayout = { //determines layout for squares in a specified rectangle, with spacing
	TILE_SPACING: DEFAULT_TILE_SPACING,
	HEADER_SZ: DEFAULT_HEADER_SZ,
	genLayout(nodes, x0, y0, w, h, hideHeader){
		//get number-of-columns with highest occupied-fraction of rectangles with aspect-ratio w/h
			//account for tile-spacing?, account for parent-box-border?, cache results?,
		let hOffset = (hideHeader ? 0 : this.HEADER_SZ);
		let numTiles = nodes.length, ar = w/(h - hOffset);
		let numCols, numRows, bestFrac = 0;
		for (let nc = 1; nc <= numTiles; nc++){
			let nr = Math.ceil(numTiles/nc);
			let ar2 = nc/nr;
			let frac = ar > ar2 ? ar2/ar : ar/ar2;
			if (frac > bestFrac){
				bestFrac = frac;
				numCols = nc;
				numRows = nr;
			}
		}
		//compute other parameters
		let tileSz = Math.min(
			((w - this.TILE_SPACING) / numCols) - this.TILE_SPACING,
			((h - this.TILE_SPACING - hOffset) / numRows) - this.TILE_SPACING);
		//determine layout
		return {
			coords: Object.fromEntries(
				nodes.map((el, idx) => [el.tolNode.name, {
					x: x0 + (idx % numCols)*(tileSz + this.TILE_SPACING) + this.TILE_SPACING,
					y: y0 + Math.floor(idx / numCols)*(tileSz + this.TILE_SPACING) + this.TILE_SPACING + hOffset,
					w: tileSz,
					h: tileSz
				}])
			),
			w: numCols * (tileSz + this.TILE_SPACING) + this.TILE_SPACING,
			h: numRows * (tileSz + this.TILE_SPACING) + this.TILE_SPACING + hOffset,
		};
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
	TILE_SPACING: DEFAULT_TILE_SPACING,
	HEADER_SZ: DEFAULT_HEADER_SZ,
	genLayout(nodes, x0, y0, w, h, hideHeader){
		if (nodes.every(e => e.children.length == 0)){
			return staticSqrLayout.genLayout(nodes, x0, y0, w, h, hideHeader);
		}
		//if a node has children, find 'best' number-of-columns to use
		let hOffset = (hideHeader ? 0 : this.HEADER_SZ);
		let numChildren = nodes.length;
		let numCols, bestScore = Number.NEGATIVE_INFINITY, numRows, rowProps, colProps;
		for (let nc = 1; nc <= numChildren; nc++){
			let nr = Math.ceil(numChildren/nc);
			//create grid representing each node's tileCount (0 for no tile)
			let grid = Array(nr).fill().map(e => Array(nc).fill(0));
			for (let i = 0; i < numChildren; i++){
				grid[Math.floor(i / nc)][i % nc] = nodes[i].tileCount;
			}
			//get totals across each row/column divided by tileCount total
			let totalTileCount = nodes.map(e => e.tileCount).reduce((x,y) => x+y);
			let rProps = grid.map(row => row.reduce((x, y) => x+y) / totalTileCount);
			let cProps = [...Array(nc).keys()].map(c =>
				[...Array(nr).keys()].map(r => grid[r][c]).reduce((x,y) => x+y) / totalTileCount);
			//get score
			let score = 0;
			for (let i = 0; i < numChildren; i++){ //get occupied-fraction //account for tile-spacing?
				let cellW = (w - this.TILE_SPACING) * cProps[i % nc];
				let cellH = (h - this.TILE_SPACING - hOffset) * rProps[Math.floor(i / nc)];
				let ar = cellW / cellH;
				let ar2 = nodes[i].arFromArea(cellW, cellH);
				let frac = ar > ar2 ? ar2/ar : ar/ar2;
				score += frac * (cellW * cellH);
			}
			////alternative score-metric
			//for (let r = 0; r < nr; r++){
			//	for (let c = 0; c < nc; c++){
			//		if (grid[r][c] > 0){
			//			score -= Math.abs(grid[r][c] - rProps[r]*cProps[c]);
			//		}
			//	}
			//}
			if (score > bestScore){
				bestScore = score;
				numCols = nc;
				numRows = nr;
				rowProps = rProps;
				colProps = cProps;
			}
		}
		//determine layout
		let rowNetProps = [0];
		for (let i = 0; i < rowProps.length-1; i++){
			rowNetProps.push(rowNetProps[i] + rowProps[i]);
		}
		let colNetProps = [0];
		for (let i = 0; i < colProps.length-1; i++){
			colNetProps.push(colNetProps[i] + colProps[i]);
		}
		return {
			coords: Object.fromEntries(
				nodes.map((el, idx) => {
					let cellW = colProps[idx % numCols]*(w - this.TILE_SPACING);
					let cellH = rowProps[Math.floor(idx / numCols)]*(h - hOffset - this.TILE_SPACING);
					let cellAR = cellW / cellH;
					return [el.tolNode.name, {
						x: x0 + colNetProps[idx % numCols]*(w - this.TILE_SPACING) + this.TILE_SPACING,
						y: y0 + rowNetProps[Math.floor(idx / numCols)]*(h - hOffset - this.TILE_SPACING) + 
							this.TILE_SPACING + hOffset,
						w: (el.children.length == 0 ? (cellAR>1 ? cellW * 1/cellAR : cellW) : cellW) - this.TILE_SPACING,
						h: (el.children.length == 0 ? (cellAR>1 ? cellH : cellH * cellAR) : cellH) - this.TILE_SPACING
					}];
				})
			),
			w: w,
			h: h
		};
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
			tree.arFromArea = (w, h) => 1;
		} else {
			tree.tileCount = tree.children.map(e => e.tileCount).reduce((x,y) => x+y);
			if (tree.children.every(e => e.children.length == 0)){
				tree.arFromArea = (w, h) => {
					let layout = staticSqrLayout.genLayout(tree.children, 0, 0, w, h, tree.hideHeader);
					return layout.w / layout.h;
				}
			} else {
				tree.arFromArea = (w, h) => w/h;
			}
		}
	}
};
const sweepToSideLayout = {
	TILE_SPACING: DEFAULT_TILE_SPACING,
	HEADER_SZ: DEFAULT_HEADER_SZ,
	genLayout(nodes, x0, y0, w, h, hideHeader){
		//separate leaf and non-leaf nodes
		let leaves = [], nonLeaves = [];
		nodes.forEach(e => (e.children.length == 0 ? leaves : nonLeaves).push(e));
		//determine layout
		if (nonLeaves.length == 0){ //if all leaves, use squares-layout
			return staticSqrLayout.genLayout(nodes, x0, y0, w, h, hideHeader);
		} else { //if some non-leaves, use rect-layout
			if (leaves.length == 0){
				return staticRectLayout.genLayout(nonLeaves, x0, y0, w, h, hideHeader);
			} else {
				//get swept-area layout
				let ratio = leaves.length / (leaves.length + nonLeaves.map(e => e.tileCount).reduce((x,y) => x+y));
				let leavesLayout = staticSqrLayout.genLayout(leaves, x0, y0, w*ratio, h, hideHeader);
				//get remaining-area layout, with shrunk-to-content-right-edge swept-area
				let x02 = x0 + leavesLayout.w - this.TILE_SPACING;
				let w2 = w - leavesLayout.w + this.TILE_SPACING;
				//let nonLeavesLayout = staticSqrLayout.genLayout(nonLeaves, x02, y0, w2, h, hideHeader);
				let nonLeavesLayout = staticRectLayout.genLayout(nonLeaves, x02, y0, w2, h, hideHeader);
				return {coords: {...leavesLayout.coords, ...nonLeavesLayout.coords}, w: w, h: h}
			}
		}
	},
	initLayoutInfo(tree){
		staticRectLayout.initLayoutInfo(tree);
	},
	updateLayoutInfoOnExpand(nodeList){
		staticRectLayout.updateLayoutInfoOnExpand(nodeList);
	},
	updateLayoutInfoOnCollapse(nodeList){
		staticRectLayout.updateLayoutInfoOnCollapse(nodeList);
	}
};
let defaultLayout = sweepToSideLayout;

function initTree(tol, lvl, layout = defaultLayout){
	let tree = {tolNode: tol, children: []};
	initTreeRec(tree, lvl);
	layout.initLayoutInfo(tree)
	return tree;
}
function initTreeRec(tree, lvl){
	if (lvl > 0){
		tree.children = tree.tolNode.children.map(e => initTreeRec({tolNode: e, children: []}, lvl-1));
	}
	return tree;
}
