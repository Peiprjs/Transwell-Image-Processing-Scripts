macro "Batch Processing" {
    inputDir = getDirectory("Choose the main Input directory");
    if (inputDir == "") {
        exit("No directory selected.");
    }

    processMainDirectory(inputDir);
    showMessage("Processing Complete!");
}

function processMainDirectory(inputDir) {
    processDirectoryRecursive(inputDir, 0);
}

function processDirectoryRecursive(currentDir, depth) {
    if (depth > 10) return;

    list = getFileList(currentDir);

    for (i = 0; i < list.length; i++) {
        if (File.isDirectory(currentDir + list[i])) {
            subDir = currentDir + list[i];
            if (depth < 3) {
                processSubfolder(subDir);
                processDirectoryRecursive(subDir, depth + 1);
            }
        }
    }
}

function processSubfolder(subDir) {
    fileList = getFileList(subDir);
    dapiFile = "";
    dapiName = "";
    zo1File = "";
    zo1Name = "";
    occlFile = "";
    occlName = "";

    // Locate exactly 3 image files containing "DAPI", "ZO1", and "OCCL"
    for (j = 0; j < fileList.length; j++) {
        fileName = fileList[j];
        if (indexOf(fileName, "DAPI") >= 0) {
            dapiFile = subDir + fileName;
            dapiName = fileName;
        } else if (indexOf(fileName, "ZO1") >= 0) {
            zo1File = subDir + fileName;
            zo1Name = fileName;
        } else if (indexOf(fileName, "OCCL") >= 0) {
            occlFile = subDir + fileName;
            occlName = fileName;
        }
    }

    if (dapiFile != "" && zo1File != "" && occlFile != "") {
        open(dapiFile);
        dapiTitle = getTitle();

        open(zo1File);
        zo1Title = getTitle();

        open(occlFile);
        occlTitle = getTitle();

        processImagesAndMerge(dapiTitle, zo1Title, occlTitle);

        compositePrefix = getCompositePrefix(dapiName, "DAPI");
        if (compositePrefix == "") compositePrefix = getCompositePrefix(zo1Name, "ZO1");
        if (compositePrefix == "") compositePrefix = getCompositePrefix(occlName, "OCCL");

        saveAs("Tiff", subDir + compositePrefix + "Merged_Composite.tif");
        saveAs("PNG", subDir + compositePrefix + "Merged_Composite.png");

        run("Close All");
    } else {
        print("Missing required files (DAPI, ZO1, OCCL) in " + subDir);
    }
}

function getCompositePrefix(fileName, marker) {
    markerIndex = indexOf(fileName, marker);
    if (markerIndex > 0) {
        return substring(fileName, 0, markerIndex);
    }
    return "";
}


function processImagesAndMerge(dapiTitle, zo1Title, occlTitle) {
    selectWindow(dapiTitle);
    run("Subtract Background...", "rolling=50 sliding");
    run("Enhance Contrast...", "saturated=0.35 equalize");

    selectWindow(zo1Title);
    run("Subtract Background...", "rolling=50 sliding");
    run("Enhance Contrast...", "saturated=0.35 equalize");

    selectWindow(occlTitle);
    run("Subtract Background...", "rolling=50 sliding");
    run("Enhance Contrast...", "saturated=0.35 equalize");

    // c1 (Red) = OCCL
    // c2 (Green) = ZO1
    // c3 (Blue) = DAPI
    mergeCmd = "c1=[" + occlTitle + "] c2=[" + zo1Title + "] c3=[" + dapiTitle + "] create";
    run("Merge Channels...", mergeCmd);
}
