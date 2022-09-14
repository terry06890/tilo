/*
 * Project-wide globals
 */

import {TolNode} from './tol';

// For server requests
const SERVER_DATA_URL = (new URL(window.location.href)).origin + '/data/'
const SERVER_IMG_PATH = '/tol_data/img/'
export async function queryServer(params: URLSearchParams){
	// Construct URL
	const url = new URL(SERVER_DATA_URL);
	url.search = params.toString();
	// Query server
	let responseObj;
	try {
		const response = await fetch(url.toString());
		responseObj = await response.json();
	} catch (error){
		console.log(`Error with querying ${url.toString()}: ${error}`);
		return null;
	}
	return responseObj;
}
export function getImagePath(imgName: string): string {
	return SERVER_IMG_PATH + imgName.replaceAll('\'', '\\\'');
}
// For server search responses
export type SearchSugg = { // Represents a search-string suggestion
	name: string,
	canonicalName: string | null,
	pop: number,
};
export type SearchSuggResponse = { // Holds search suggestions and an indication of if there was more
	suggs: SearchSugg[],
	hasMore: boolean,
};
// For server tile-info responses
export type DescInfo = {
	text: string,
	wikiId: number,
	fromRedirect: boolean,
	fromDbp: boolean,
};
export type ImgInfo = {
	id: number,
	src: string,
	url: string,
	license: string,
	artist: string,
	credit: string,
};
export type NodeInfo = {
	tolNode: TolNode,
	descInfo: null | DescInfo,
	imgInfo: null | ImgInfo,
};
export type InfoResponse = {
	nodeInfo: NodeInfo,
	subNodesInfo: [] | [NodeInfo | null, NodeInfo | null],
};

// Used by auto-mode and tutorial-pane
export type Action =
	'expand' | 'collapse' | 'expandToView' | 'unhideAncestor' |
	'tileInfo' | 'search' | 'autoMode' | 'settings' | 'help';
