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

        compositePrefix = getCompositePrefix(dapiName, "DAPI");
        if (compositePrefix == "") compositePrefix = getCompositePrefix(zo1Name, "ZO1");
        if (compositePrefix == "") compositePrefix = getCompositePrefix(occlName, "OCCL");

        processImagesAndMerge(dapiTitle, zo1Title, occlTitle, subDir, compositePrefix);

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


function processImagesAndMerge(dapiTitle, zo1Title, occlTitle, subDir, compositePrefix) {
    selectWindow(dapiTitle);
    run("Subtract Background...", "rolling=50 sliding");
    run("Enhance Contrast...", "saturated=0.35 equalize");

    selectWindow(zo1Title);
    run("Subtract Background...", "rolling=50 sliding");
    run("Enhance Contrast...", "saturated=0.35 equalize");

    selectWindow(occlTitle);
    run("Subtract Background...", "rolling=50 sliding");
    run("Enhance Contrast...", "saturated=0.35 equalize");

    // DAPI (Blue) and ZO1 (Green)
    mergeCmd1 = "c2=[" + zo1Title + "] c3=[" + dapiTitle + "] create keep";
    run("Merge Channels...", mergeCmd1);
    saveAs("Tiff", subDir + compositePrefix + "Merged_ZO1.tif");
    saveAs("PNG", subDir + compositePrefix + "Merged_ZO1.png");
    close();

    // DAPI (Blue) and OCCL (Red)
    mergeCmd2 = "c1=[" + occlTitle + "] c3=[" + dapiTitle + "] create keep";
    run("Merge Channels...", mergeCmd2);
    saveAs("Tiff", subDir + compositePrefix + "Merged_Occludin.tif");
    saveAs("PNG", subDir + compositePrefix + "Merged_Occludin.png");
    close();
}
