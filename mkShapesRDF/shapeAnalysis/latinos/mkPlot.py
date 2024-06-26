#!/usr/bin/env python

import sys

import argparse

import os
import os.path

from multiprocessing import Process
from mkShapesRDF.shapeAnalysis.latinos.PlotFactory import PlotFactory

argv = sys.argv
sys.argv = argv[:1]


# X. Janssen - 21 March 2018
# PlotFactory splitted from this file and moved to python to be able to use in other scripts (mkACPlot.py)
#


if __name__ == "__main__":
    main()


def defaultParser():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--scaleToPlot",
        dest="scaleToPlot",
        help="scale of maxY to maxHistoY",
        default=3.0,
        type=float,
    )
    parser.add_argument(
        "--minLogC", dest="minLogC", help="min Y in log plots", default=0.01, type=float
    )
    parser.add_argument(
        "--maxLogC", dest="maxLogC", help="max Y in log plots", default=100, type=float
    )
    parser.add_argument(
        "--minLogCratio",
        dest="minLogCratio",
        help="min Y in log ratio plots",
        default=0.001,
        type=float,
    )
    parser.add_argument(
        "--maxLogCratio",
        dest="maxLogCratio",
        help="max Y in log ratio plots",
        default=10,
        type=float,
    )
    parser.add_argument(
        "--maxLinearScale",
        dest="maxLinearScale",
        help="scale factor for max Y in linear plots (1.45 magic number as default)",
        default=1.45,
        type=float,
    )
    parser.add_argument(
        "--outputDirPlots", dest="outputDirPlots", help="output directory", default="./"
    )
    parser.add_argument(
        "--inputFile",
        dest="inputFile",
        help="input file with histograms",
        default="input.root",
    )
    parser.add_argument(
        "--tag",
        dest="tag",
        help="Tag used for the shape file name. Used if inputFile is a directory",
        default=None,
    )
    parser.add_argument(
        "--nuisancesFile",
        dest="nuisancesFile",
        help="file with nuisances configurations",
        default=None,
    )

    parser.add_argument(
        "--onlyVariable",
        dest="onlyVariable",
        help="draw only one variable (may be needed in post-fit plots)",
        default=None,
    )
    parser.add_argument(
        "--onlyCut",
        dest="onlyCut",
        help="draw only one cut phase space (may be needed in post-fit plots)",
        default=None,
    )
    parser.add_argument(
        "--onlyPlot",
        dest="onlyPlot",
        help="draw only specified plot type (comma-separated c, cratio, and/or cdifference)",
        default=None,
    )

    parser.add_argument(
        "--linearOnly",
        dest="linearOnly",
        help="Make linear plot only.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--logOnly",
        dest="logOnly",
        help="Make log plot only.",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--fileFormats",
        dest="fileFormats",
        help='Output plot file formats (comma-separated png, pdf, root, C, and/or eps). Default "png,root"',
        default="png,root",
    )

    parser.add_argument(
        "--plotNormalizedIncludeData",
        dest="plotNormalizedIncludeData",
        help="plot also normalized distributions for data, for shape comparison purposes",
        default=None,
    )
    parser.add_argument(
        "--plotNormalizedDistributions",
        dest="plotNormalizedDistributions",
        help="plot also normalized distributions for optimization purposes",
        action="store_true",
        default=None,
    )
    parser.add_argument(
        "--plotNormalizedDistributionsTHstack",
        dest="plotNormalizedDistributionsTHstack",
        help="plot also normalized distributions for optimization purposes, with stacked sig and bkg",
        action="store_true",
        default=None,
    )

    parser.add_argument(
        "--showIntegralLegend",
        dest="showIntegralLegend",
        help="show the integral, the yields, in the legend",
        default=0,
        type=float,
    )

    parser.add_argument(
        "--showRelativeRatio",
        dest="showRelativeRatio",
        help="draw instead of data-expected, (data-expected) / expected",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--showDataMinusBkgOnly",
        dest="showDataMinusBkgOnly",
        help="draw instead of data-expected, data-expected background only",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--removeWeight",
        dest="removeWeight",
        help="Remove weight S/B for PR plots, just do the sum",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--invertXY",
        dest="invertXY",
        help="Invert the weighting for X <-> Y. Instead of slices along Y, do slices along X",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--postFit",
        dest="postFit",
        help="Plot sum of post-fit backgrounds, and the data/post-fit ratio.",
        default="n",
    )

    parser.add_argument(
        "--skipMissingNuisance",
        dest="skipMissingNuisance",
        help="Do not trigger errors if a nuisance is missing. To be used with absolute care!!!",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--removeMCStat",
        dest="removeMCStat",
        help="Do not plot the MC statistics contribution in the uncertainty band",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--extraLegend",
        dest="extraLegend",
        help="User-specified additional legend",
        default=None,
    )

    parser.add_argument(
        "--customize",
        dest="customizeKey",
        help="Optional parameters for the customizations script",
        default=None,
    )
    parser.add_argument(
        "--plotFancy",
        dest="plotFancy",
        help="Plot fancy data - bkg plot",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--NoPreliminary",
        dest="NoPreliminary",
        help="Remove preliminary status in plots",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--RemoveAllMC",
        dest="RemoveAllMC",
        help="Remove all MC in legend",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--parallelPlotting",
        dest="parallelPlotting",
        help="Plot each cut in parallel",
        action="store_true",
        default=False,
    )
    return parser


def main():
    sys.argv = argv

    opt = defaultParser().parse_args()

    print("")
    # print("          configuration file =", opt.pycfg)
    # print("                        lumi =", opt.lumi)
    print("                   inputFile =", opt.inputFile)
    print("              outputDirPlots =", opt.outputDirPlots)
    print(" plotNormalizedDistributions =", opt.plotNormalizedDistributions)
    print("   plotNormalizedIncludeData =", opt.plotNormalizedIncludeData)
    print(
        " plotNormalizedDistributionsTHstack =", opt.plotNormalizedDistributionsTHstack
    )
    print("          showIntegralLegend =", opt.showIntegralLegend)
    print("                 scaleToPlot =", opt.scaleToPlot)
    print("                     minLogC =", opt.minLogC)
    print("                     maxLogC =", opt.maxLogC)
    print("                minLogCratio =", opt.minLogCratio)
    print("                maxLogCratio =", opt.maxLogCratio)
    print("           showRelativeRatio =", opt.showRelativeRatio)
    print("        showDataMinusBkgOnly =", opt.showDataMinusBkgOnly)
    print("                removeWeight =", opt.removeWeight)
    print("                    invertXY =", opt.invertXY)
    print("        skipMissingNuisance  =", opt.skipMissingNuisance)
    print("                    postFit  =", opt.postFit)
    print("               removeMCStat  =", opt.removeMCStat)
    print("                  plotFancy  =", opt.plotFancy)
    print("              NoPreliminary  =", opt.NoPreliminary)
    print("                RemoveAllMC  =", opt.RemoveAllMC)
    print("           parallelPlotting  =", opt.parallelPlotting)
    print("")

    opt.scaleToPlot = float(opt.scaleToPlot)
    opt.minLogC = float(opt.minLogC)
    opt.maxLogC = float(opt.maxLogC)

    opt.minLogCratio = float(opt.minLogCratio)
    opt.maxLogCratio = float(opt.maxLogCratio)

    #    if not opt.debug:
    #        pass
    #    elif opt.debug == 2:
    #        print 'Logging level set to DEBUG (%d)' % opt.debug
    #        logging.basicConfig( level=logging.DEBUG )
    #    elif opt.debug == 1:
    #        print 'Logging level set to INFO (%d)' % opt.debug
    #        logging.basicConfig( level=logging.INFO )

    # samples = {}
    # samples = OrderedDict()
    #    if opt.samplesFile == None :
    #      print " Please provide the samples structure (not strictly needed in mkPlot, since list of samples read from plot.py) "
    #    elif os.path.exists(opt.samplesFile) :
    #      # This line is needed for mkplot not to look for samples in eos.
    #      # Imagine the samples have been removed in eos, but the file with histograms
    #      # has been already generated, there is no need to check the existence of the samples on eos
    #      # NB: in samples.py the function "nanoGetSampleFiles" must handle this, if needed
    #      _samples_noload = True
    #      handle = open(opt.samplesFile,'r')
    #      exec(handle)
    #      handle.close()

    #    cuts = {}
    #    if os.path.exists(opt.cutsFile) :
    #      handle = open(opt.cutsFile,'r')
    #      exec(handle)
    #      handle.close()
    #
    #    variables = {}
    #    if os.path.exists(opt.variablesFile) :
    #      handle = open(opt.variablesFile,'r')
    #      exec(handle)
    #      handle.close()
    #
    #    nuisances = {}
    #    if opt.nuisancesFile == None :
    #      print " Please provide the nuisances structure if you want to add nuisances "
    #    elif os.path.exists(opt.nuisancesFile) :
    #      handle = open(opt.nuisancesFile,'r')
    #      exec(handle)
    #      handle.close()

    import mkShapesRDF.shapeAnalysis.latinos.LatinosUtils as utils

    # import glob

    # import json
    # lFile = list(filter(lambda k: os.path.isfile(k), glob.glob('configs/*json')))
    # lFile.sort(key= lambda x: os.path.getmtime(x))
    # lFile = lFile[-1]
    # with open(lFile) as file:
    #     d = json.load(file)

    from mkShapesRDF.shapeAnalysis.ConfigLib import ConfigLib

    global plot
    global cuts
    configsFolder = "configs"
    # ConfigLib.loadLatestJSON('configs', globals())
    ConfigLib.loadLatestPickle(os.path.abspath(configsFolder), globals())
    # ConfigLib.loadDict(d, globals())
    print(dir())
    print(globals().keys())

    cuts = cuts["cuts"]
    groupPlot = plot["groupPlot"]
    legend = plot["legend"]
    plot = plot["plot"]
    inputFile = outputFolder + "/" + outputFile

    subsamplesmap = utils.flatten_samples(samples)
    categoriesmap = utils.flatten_cuts(cuts)

    utils.update_variables_with_categories(variables, categoriesmap)
    utils.update_nuisances_with_subsamples(nuisances, subsamplesmap)
    utils.update_nuisances_with_categories(nuisances, categoriesmap)

    # check if only one cut or only one variable
    # is requested, and filter th elist of cuts and variables
    # using this piece of information

    if opt.onlyVariable is not None:
        list_to_remove = []
        for variableName, variable in variables.iteritems():
            if variableName != opt.onlyVariable:
                list_to_remove.append(variableName)
        for toRemove in list_to_remove:
            del variables[toRemove]

        print(" variables = ", variables)

    if opt.onlyCut is not None:
        list_to_remove = []
        for cutName, cutExtended in cuts.iteritems():
            if cutName not in opt.onlyCut:
                list_to_remove.append(cutName)
        for toRemove in list_to_remove:
            del cuts[toRemove]

        print(" cuts = ", cuts)

    #    groupPlot = OrderedDict()
    #    plot = {}
    #    legend = {}
    #    if os.path.exists(opt.plotFile) :
    #      handle = open(opt.plotFile,'r')
    #      exec(handle)
    #      handle.close()
    # energy = '13TeV'
    # sys.exit()
    # =====================
    def launch_plot(
        inputFile,
        outputDirPlots,
        variables,
        cuts,
        samples,
        plot,
        nuisances,
        legend,
        groupPlot,
    ):
        factory = PlotFactory()
        factory._tag = tag
        # factory._energy    = opt.energy
        factory._lumi = lumi
        factory._plotNormalizedDistributions = opt.plotNormalizedDistributions
        factory._plotNormalizedIncludeData = opt.plotNormalizedIncludeData
        factory._plotNormalizedDistributionsTHstack = (
            opt.plotNormalizedDistributionsTHstack
        )
        factory._showIntegralLegend = opt.showIntegralLegend

        if opt.onlyPlot is not None:
            factory._plotsToWrite = opt.onlyPlot.split(",")
        factory._plotLinear = opt.linearOnly or not opt.logOnly
        factory._plotLog = opt.logOnly or not opt.linearOnly

        factory._scaleToPlot = opt.scaleToPlot
        factory._minLogC = opt.minLogC
        factory._maxLogC = opt.maxLogC
        factory._minLogCratio = opt.minLogCratio
        factory._maxLogCratio = opt.maxLogCratio
        factory._maxLinearScale = opt.maxLinearScale

        factory._minLogCdifference = opt.minLogCratio
        factory._maxLogCdifference = opt.maxLogCratio

        factory._showRelativeRatio = opt.showRelativeRatio
        factory._showDataMinusBkgOnly = opt.showDataMinusBkgOnly

        factory._removeWeight = opt.removeWeight

        factory._invertXY = opt.invertXY

        factory._fileFormats = opt.fileFormats.split(",")

        factory._postFit = opt.postFit

        factory._removeMCStat = opt.removeMCStat
        factory._plotFancy = opt.plotFancy
        factory._SkipMissingNuisance = opt.skipMissingNuisance

        factory._extraLegend = opt.extraLegend
        factory._preliminary = not opt.NoPreliminary
        factory._removeAllMC = opt.RemoveAllMC

        factory.makePlot(
            inputFile,
            outputDirPlots,
            variables,
            cuts,
            samples,
            plot,
            nuisances,
            legend,
            groupPlot,
        )

    # ===============================

    if opt.parallelPlotting:
        for cut in cuts:
            p = Process(
                target=launch_plot(
                    inputFile,
                    plotPath,
                    variables,
                    [cut],
                    samples,
                    plot,
                    nuisances,
                    legend,
                    groupPlot,
                )
            )
            p.start()
    else:
        launch_plot(
            inputFile,
            plotPath,
            variables,
            cuts,
            samples,
            plot,
            nuisances,
            legend,
            groupPlot,
        )
