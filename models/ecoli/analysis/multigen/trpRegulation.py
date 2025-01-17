"""
Plot trp regulation

@author: Derek Macklin
@organization: Covert Lab, Department of Bioengineering, Stanford University
@date: Created 6/17/2016
"""

from __future__ import absolute_import
from __future__ import division

import os

import numpy as np
from matplotlib import pyplot as plt
import cPickle

from wholecell.io.tablereader import TableReader
from wholecell.utils import units
from models.ecoli.analysis.AnalysisPaths import AnalysisPaths
from wholecell.analysis.analysis_tools import exportFigure
from models.ecoli.analysis import multigenAnalysisPlot


class Plot(multigenAnalysisPlot.MultigenAnalysisPlot):
	def do_plot(self, seedOutDir, plotOutDir, plotOutFileName, simDataFile, validationDataFile, metadata):
		if not os.path.isdir(seedOutDir):
			raise Exception, "seedOutDir does not currently exist as a directory"

		if not os.path.exists(plotOutDir):
			os.mkdir(plotOutDir)

		ap = AnalysisPaths(seedOutDir, multi_gen_plot = True)

		allDirs = ap.get_cells()

		# Load data from KB
		sim_data = cPickle.load(open(simDataFile, "rb"))
		nAvogadro = sim_data.constants.nAvogadro
		cellDensity = sim_data.constants.cellDensity

		recruitmentColNames = sim_data.process.transcription_regulation.recruitmentColNames
		tfs = sorted(set([x.split("__")[-1] for x in recruitmentColNames if x.split("__")[-1] != "alpha"]))
		trpRIndex = [i for i, tf in enumerate(tfs) if tf == "CPLX-125"][0]

		tfBoundIds = [target + "__CPLX-125" for target in sim_data.tfToFC["CPLX-125"].keys()]
		synthProbIds = [target + "[c]" for target in sim_data.tfToFC["CPLX-125"].keys()]

		plt.figure(figsize = (10, 15))
		nRows = 10

		for simDir in allDirs:
			simOutDir = os.path.join(simDir, "simOut")
			# Load time
			initialTime = 0#TableReader(os.path.join(simOutDir, "Main")).readAttribute("initialTime")
			time = TableReader(os.path.join(simOutDir, "Main")).readColumn("time") - initialTime

			# Load mass data
			# Total cell mass is needed to compute concentrations (since we have cell density)
			# Protein mass is needed to compute the mass fraction of the proteome that is trpA
			massReader = TableReader(os.path.join(simOutDir, "Mass"))
			cellMass = units.fg * massReader.readColumn("cellMass")
			proteinMass = units.fg * massReader.readColumn("proteinMass")
			massReader.close()

			# Load data from ribosome data listener
			ribosomeDataReader = TableReader(os.path.join(simOutDir, "RibosomeData"))
			nTrpATranslated = ribosomeDataReader.readColumn("numTrpATerminated")
			ribosomeDataReader.close()

			# Load data from bulk molecules
			bulkMoleculesReader = TableReader(os.path.join(simOutDir, "BulkMolecules"))
			bulkMoleculeIds = bulkMoleculesReader.readAttribute("objectNames")

			# Get the concentration of intracellular trp
			trpId = ["TRP[c]"]
			trpIndex = np.array([bulkMoleculeIds.index(x) for x in trpId])
			trpCounts = bulkMoleculesReader.readColumn("counts")[:, trpIndex].reshape(-1)
			trpMols = 1. / nAvogadro * trpCounts
			volume = cellMass / cellDensity
			trpConcentration = trpMols * 1. / volume

			# Get the amount of active trpR (that isn't promoter bound)
			trpRActiveId = ["CPLX-125[c]"]
			trpRActiveIndex = np.array([bulkMoleculeIds.index(x) for x in trpRActiveId])
			trpRActiveCounts = bulkMoleculesReader.readColumn("counts")[:, trpRActiveIndex].reshape(-1)

			# Get the amount of inactive trpR
			trpRInactiveId = ["PC00007[c]"]
			trpRInactiveIndex = np.array([bulkMoleculeIds.index(x) for x in trpRInactiveId])
			trpRInactiveCounts = bulkMoleculesReader.readColumn("counts")[:, trpRInactiveIndex].reshape(-1)

			# Get the amount of monomeric trpR
			trpRMonomerId = ["PD00423[c]"]
			trpRMonomerIndex = np.array([bulkMoleculeIds.index(x) for x in trpRMonomerId])
			trpRMonomerCounts = bulkMoleculesReader.readColumn("counts")[:, trpRMonomerIndex].reshape(-1)

			# Get the promoter-bound status for all regulated genes
			tfBoundIndex = np.array([bulkMoleculeIds.index(x) for x in tfBoundIds])
			tfBoundCounts = bulkMoleculesReader.readColumn("counts")[:, tfBoundIndex]

			# Get the amount of monomeric trpA
			trpAProteinId = ["TRYPSYN-APROTEIN[c]"]
			trpAProteinIndex = np.array([bulkMoleculeIds.index(x) for x in trpAProteinId])
			trpAProteinCounts = bulkMoleculesReader.readColumn("counts")[:, trpAProteinIndex].reshape(-1)

			# Get the amount of complexed trpA
			trpABComplexId = ["TRYPSYN[c]"]
			trpABComplexIndex = np.array([bulkMoleculeIds.index(x) for x in trpABComplexId])
			trpABComplexCounts = bulkMoleculesReader.readColumn("counts")[:, trpABComplexIndex].reshape(-1)

			# Get the amount of trpA mRNA
			trpARnaId = ["EG11024_RNA[c]"]
			trpARnaIndex = np.array([bulkMoleculeIds.index(x) for x in trpARnaId])
			trpARnaCounts = bulkMoleculesReader.readColumn("counts")[:, trpARnaIndex].reshape(-1)

			bulkMoleculesReader.close()

			# Compute total counts and concentration of trpA in monomeric and complexed form
			# (we know the stoichiometry)
			trpAProteinTotalCounts = trpAProteinCounts + 2 * trpABComplexCounts
			trpAProteinTotalMols = 1. / nAvogadro * trpAProteinTotalCounts
			trpAProteinTotalConcentration = trpAProteinTotalMols * 1. / volume

			# Compute concentration of trpA mRNA
			trpARnaMols = 1. / nAvogadro * trpARnaCounts
			trpARnaConcentration = trpARnaMols * 1. / volume

			# Compute the trpA mass in the cell
			trpAMw = sim_data.getter.getMass(trpAProteinId)
			trpAMass = 1. / nAvogadro * trpAProteinTotalCounts * trpAMw

			# Compute the proteome mass fraction
			proteomeMassFraction = trpAMass.asNumber(units.fg) / proteinMass.asNumber(units.fg)

			# Get the synthesis probability for all regulated genes
			rnaSynthProbReader = TableReader(os.path.join(simOutDir, "RnaSynthProb"))

			rnaIds = rnaSynthProbReader.readAttribute("rnaIds")
			synthProbIndex = np.array([rnaIds.index(x) for x in synthProbIds])
			synthProbs = rnaSynthProbReader.readColumn("rnaSynthProb")[:, synthProbIndex]

			trpRBound = rnaSynthProbReader.readColumn("nActualBound")[:,trpRIndex]

			rnaSynthProbReader.close()

			# Calculate total trpR - active, inactive, bound and monomeric
			trpRTotalCounts = 2 * (trpRActiveCounts + trpRInactiveCounts + trpRBound) + trpRMonomerCounts

			# Compute moving averages
			width = 100

			tfBoundCountsMA = np.array([np.convolve(tfBoundCounts[:,i], np.ones(width) / width, mode = "same")
					for i in range(tfBoundCounts.shape[1])]).T
			synthProbsMA = np.array([np.convolve(synthProbs[:,i], np.ones(width) / width, mode = "same")
					for i in range(synthProbs.shape[1])]).T


			##############################################################
			ax = plt.subplot(nRows, 1, 1)
			ax.plot(time, trpConcentration.asNumber(units.umol / units.L), color = '#0d71b9')
			plt.ylabel("Internal TRP Conc. [uM]", fontsize = 6)

			ymin, ymax = ax.get_ylim()
			ax.set_yticks([ymin, ymax])
			ax.set_yticklabels(["%0.0f" % ymin, "%0.0f" % ymax])
			ax.spines['top'].set_visible(False)
			ax.spines['bottom'].set_visible(False)
			ax.xaxis.set_ticks_position('none')
			ax.tick_params(which = 'both', direction = 'out', labelsize = 6)
			ax.set_xticks([])
			##############################################################

			##############################################################
			ax = plt.subplot(nRows, 1, 2)
			ax.plot(time, trpRActiveCounts)
			ax.plot(time, trpRInactiveCounts)
			ax.plot(time, trpRTotalCounts)
			plt.ylabel("TrpR Counts", fontsize = 6)
			plt.legend(["Active (dimer)", "Inactive (dimer)", "Total (monomeric)"], fontsize = 6)

			ymin, ymax = ax.get_ylim()
			ax.set_yticks([ymin, ymax])
			ax.set_yticklabels(["%0.0f" % ymin, "%0.0f" % ymax])
			ax.spines['top'].set_visible(False)
			ax.spines['bottom'].set_visible(False)
			ax.xaxis.set_ticks_position('none')
			ax.tick_params(which = 'both', direction = 'out', labelsize=6)
			ax.set_xticks([])
			##############################################################

			##############################################################
			ax = plt.subplot(nRows, 1, 3)
			ax.plot(time, tfBoundCountsMA, color = '#0d71b9')
			#comment out color in order to see colors per generation
			plt.ylabel("TrpR Bound To Promoters\n(Moving Average)", fontsize = 6)

			ymin, ymax = ax.get_ylim()
			ax.set_yticks([ymin, ymax])
			ax.set_yticklabels(["%0.0f" % ymin, "%0.0f" % ymax])
			ax.spines['top'].set_visible(False)
			ax.spines['bottom'].set_visible(False)
			ax.xaxis.set_ticks_position('none')
			ax.tick_params(which = 'both', direction = 'out', labelsize = 6)
			ax.set_xticks([])
			##############################################################

			##############################################################
			ax = plt.subplot(nRows, 1, 4)
			ax.plot(time, synthProbsMA)
			plt.ylabel("Regulated Gene Synthesis Prob.\n(Moving Average)", fontsize = 6)

			ymin, ymax = ax.get_ylim()
			ax.set_yticks([ymin, ymax])
			ax.set_yticklabels(["%0.2e" % ymin, "%0.2e" % ymax])
			ax.spines['top'].set_visible(False)
			ax.spines['bottom'].set_visible(False)
			ax.xaxis.set_ticks_position('none')
			ax.tick_params(which = 'both', direction = 'out', labelsize = 6)
			ax.set_xticks([])
			##############################################################

			##############################################################
			ax = plt.subplot(nRows, 1, 5)
			ax.plot(time, trpAProteinTotalCounts, color = '#0d71b9')
			plt.ylabel("TrpA Counts", fontsize = 6)

			ymin, ymax = ax.get_ylim()
			ax.set_yticks([ymin, ymax])
			ax.set_yticklabels(["%0.0f" % ymin, "%0.0f" % ymax])
			ax.spines['top'].set_visible(False)
			ax.spines['bottom'].set_visible(False)
			ax.xaxis.set_ticks_position('none')
			ax.tick_params(which = 'both', direction = 'out', labelsize = 6)
			ax.set_xticks([])
			##############################################################

			##############################################################
			ax = plt.subplot(nRows, 1, 6)
			ax.plot(time, trpAProteinTotalConcentration.asNumber(units.umol / units.L), color = '#0d71b9')
			plt.ylabel("TrpA Concentration", fontsize = 6)

			ymin, ymax = ax.get_ylim()
			ax.set_yticks([ymin, ymax])
			ax.set_yticklabels(["%0.2f" % ymin, "%0.2f" % ymax])
			ax.spines['top'].set_visible(False)
			ax.spines['bottom'].set_visible(False)
			ax.xaxis.set_ticks_position('none')
			ax.tick_params(which = 'both', direction = 'out', labelsize = 6)
			ax.set_xticks([])
			##############################################################

			##############################################################
			ax = plt.subplot(nRows, 1, 7)
			ax.plot(time, trpARnaCounts, color = '#0d71b9')
			plt.ylabel("TrpA mRNA Counts", fontsize = 6)

			ymin, ymax = ax.get_ylim()
			ax.set_yticks([ymin, ymax])
			ax.set_yticklabels(["%0.0f" % ymin, "%0.0f" % ymax])
			ax.spines['top'].set_visible(False)
			ax.spines['bottom'].set_visible(False)
			ax.xaxis.set_ticks_position('none')
			ax.tick_params(which = 'both', direction = 'out', labelsize = 6)
			ax.set_xticks([])
			##############################################################

			##############################################################
			ax = plt.subplot(nRows, 1, 8)
			ax.plot(time, trpARnaConcentration.asNumber(units.umol / units.L), color = '#0d71b9')
			plt.ylabel("TrpA mRNA Concentration", fontsize = 6)

			ymin, ymax = ax.get_ylim()
			ax.set_yticks([ymin, ymax])
			ax.set_yticklabels(["%0.2e" % ymin, "%0.2e" % ymax])
			ax.spines['top'].set_visible(False)
			ax.spines['bottom'].set_visible(False)
			ax.xaxis.set_ticks_position('none')
			ax.tick_params(which = 'both', direction = 'out', labelsize = 6)
			ax.set_xticks([])
			##############################################################

			##############################################################
			ax = plt.subplot(nRows, 1, 9)
			ax.plot(time / 3600., proteomeMassFraction, color = '#0d71b9')
			plt.ylabel("TrpA MAss FRaction of Proteome", fontsize = 6)

			ymin, ymax = ax.get_ylim()
			ax.set_yticks([ymin, ymax])
			ax.set_yticklabels(["%0.2e" % ymin, "%0.2e" % ymax])
			ax.spines['top'].set_visible(False)
			ax.spines['bottom'].set_visible(False)
			# ax.xaxis.set_ticks_position('none')
			ax.tick_params(which = 'both', direction = 'out', labelsize = 6)
			ax.set_xticks(ax.get_xlim())
			##############################################################

			##############################################################
			ax = plt.subplot(nRows, 1, 10)
			ax.plot(time, nTrpATranslated, color = '#0d71b9')
			plt.ylabel("Number of TrpA translation events", fontsize = 6)

			ymin, ymax = ax.get_ylim()
			ax.set_yticks([ymin, ymax])
			ax.set_yticklabels(["%0.0f" % ymin, "%0.0f" % ymax])
			ax.spines['top'].set_visible(False)
			ax.spines['bottom'].set_visible(False)
			ax.xaxis.set_ticks_position('none')
			ax.tick_params(which = 'both', direction = 'out', labelsize = 6)
			ax.set_xticks([])
			##############################################################

		plt.subplots_adjust(hspace = 1)

		exportFigure(plt, plotOutDir, plotOutFileName, metadata)
		plt.close("all")


if __name__ == "__main__":
	Plot().cli()
