/*

This script reads the nLab content and generates a data.bin file that contains the data in a compressed format.

It is only used to generate the data.bin file, and is not used in the actual website; thus should only be run once to generate the data.bin file and not be run again.

*/

const fs = require('node:fs/promises');
const pako = require('pako');

async function gatherDataPrimitive(path, data, people) {
    // Read directory
    const files = await fs.readdir(path, {withFileTypes: true});
    
    // For each file
    await Promise.all(files.map(file => (async function() {
        let filepath = path + "/" + file.name;
        let nameExists = false;
        try {
            // Try to read the name file
            await fs.stat(filepath + "/name");
            nameExists = true;
        } catch(err) {}
        // If it exists, read the name and content
        if (nameExists) {
            let name = await fs.readFile(filepath + "/name", {encoding: "utf-8"});
            let content = await fs.readFile(filepath + "/content.md", { encoding: "utf-8" });
            let links = (content.match(/\[\[[A-Za-z0-9_\-\s]+\]\]/g) || []).map(c => c.slice(2, -2));
            let alts = [];

            let r = /\[\[\!redirects ([A-Za-z0-9\-_\s]+)\]\]/g;
            for(;;) { 
                match = r.exec(content);
                if (match == null) break;
                alts.push(match[1]);
            }
            // If the article is a person article, add it to the people set
            if (content.includes("category: people") || content.includes("category: reference") || content.includes("category: meta") ||
                content.includes("category:people") || content.includes("category:reference") || content.includes("category:meta")
                || content.includes("[[!include quantum systems -- contents]]")
                || content.includes("[[!include string theory - contents]]")
                || content.includes("[[!include physicscontents]]")
                || content.includes("[[!include fields and quanta - table]]")
// cannot exclude the following
//                || content.includes("[[!include functorial quantum field theory - contents]]")
//                || content.includes("[[!include AQFT and operator algebra contents]]")
) {
                // person article
                for (let alt of alts) {
                    people.add(alt);
                }
                people.add(name);
            } else {
                // real article
                for (let alt of alts) {
                    data[alt] = {
                        redirect: name
                    }
                };
    
                data[name] = {
                    links: links,
                    alts: alts,
                    content: content,
                };
            }
        } else if (file.isDirectory()) {
            await gatherDataPrimitive(filepath, data, people);
        }
    })()));
}

async function gatherData(path, data) {
    let people = new Set();
    // Gather data
    await gatherDataPrimitive(path, data, people);

    console.log("Remove people...");
    // Remove people from links
    for (let article in data) {
        if (data[article].links) {
            data[article].links = data[article].links.filter(name => !people.has(name));
        }
    }
}

// Main

let data = {};
(async function() {
    // Gather Data wrapper
    await gatherData("./nlab-content", data);
    // Write data to data.bin
    await fs.writeFile("data.bin", pako.deflate(new TextEncoder().encode(JSON.stringify(data))));
})();
