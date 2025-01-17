from __future__ import absolute_import
from __future__ import division

import os

import numpy as np
from matplotlib import pyplot as plt
import matplotlib.gridspec as gridspec

from models.ecoli.analysis.AnalysisPaths import AnalysisPaths
from wholecell.io.tablereader import TableReader
from wholecell.analysis.analysis_tools import exportFigure
from wholecell.utils import units
import cPickle
from models.ecoli.analysis import multigenAnalysisPlot


class Plot(multigenAnalysisPlot.MultigenAnalysisPlot):
	def do_plot(self, seedOutDir, plotOutDir, plotOutFileName, simDataFile, validationDataFile, metadata):
		if not os.path.isdir(seedOutDir):
			raise Exception, "seedOutDir does not currently exist as a directory"

		if not os.path.exists(plotOutDir):
			os.mkdir(plotOutDir)

		ap = AnalysisPaths(seedOutDir, multi_gen_plot = True)

		# Get first cell from each generation
		firstCellLineage = []

		for gen_idx in range(ap.n_generation):
			firstCellLineage.append(ap.get_cells(generation = [gen_idx])[0])

		sim_data = cPickle.load(open(simDataFile, "rb"))

		## Get expected doubling time ##
		expected_doubling_time = sim_data.doubling_time

		fig = plt.figure()
		fig.set_size_inches(15,15)

		gs = gridspec.GridSpec(9, 5)

		ax1 = plt.subplot(gs[0,:2])
		ax1_1 = plt.subplot(gs[0,2])
		ax2 = plt.subplot(gs[1,:2])
		ax2_1 = plt.subplot(gs[1,2])
		ax3 = plt.subplot(gs[2,:2])
		ax4 = plt.subplot(gs[3,:2])
		ax5 = plt.subplot(gs[4,:2])
		ax6 = plt.subplot(gs[5,:2])
		ax7 = plt.subplot(gs[6,:2])
		ax8 = plt.subplot(gs[7,:2])
		ax8_1 = plt.subplot(gs[8,:2])

		ax9 = plt.subplot(gs[0,3:])
		ax10 = plt.subplot(gs[1,3:])
		ax11 = plt.subplot(gs[2,3:])
		ax12 = plt.subplot(gs[3,3:])
		ax13 = plt.subplot(gs[4,3:])
		ax14 = plt.subplot(gs[5,3:])
		ax15 = plt.subplot(gs[6,3:])
		ax16 = plt.subplot(gs[7,3:])


		for gen, simDir in enumerate(firstCellLineage):

			simOutDir = os.path.join(simDir, "simOut")

			## Mass growth rate ##
			time, growthRate = getMassData(simDir, ["instantaniousGrowthRate"])
			timeStep = units.s * TableReader(os.path.join(simOutDir, "Main")).readColumn("timeStepSec")
			time = units.s * time
			growthRate = (1 / units.s) * growthRate
			doublingTime = 1 / growthRate * np.log(2)

			## RNAP counts and statistics ##

			# Get free counts
			bulkMolecules = TableReader(os.path.join(simOutDir, "BulkMolecules"))
			moleculeIds = bulkMolecules.readAttribute("objectNames")
			rnapId = "APORNAP-CPLX[c]"
			rnapIndex = moleculeIds.index(rnapId)
			rnapCountsBulk = bulkMolecules.readColumn("counts")[:, rnapIndex]
			bulkMolecules.close()

			# Get active counts
			uniqueMolecules = TableReader(os.path.join(simOutDir, "UniqueMoleculeCounts"))
			rnapIndex = uniqueMolecules.readAttribute("uniqueMoleculeIds").index("activeRnaPoly")
			initialTime = TableReader(os.path.join(simOutDir, "Main")).readAttribute("initialTime")
			rnapCountsActive = uniqueMolecules.readColumn("uniqueMoleculeCounts")[:, rnapIndex]
			uniqueMolecules.close()

			# Calculate statistics
			totalRnap = rnapCountsBulk + rnapCountsActive
			fractionRnapActive = rnapCountsActive / (rnapCountsActive + rnapCountsBulk)

			## Mass fraction statistics ##

			massDataFile = TableReader(os.path.join(simOutDir, "Mass"))
			rnaMass = massDataFile.readColumn("rnaMass")
			proteinMass = massDataFile.readColumn("proteinMass")
			cellMass = massDataFile.readColumn("cellMass")

			ratioRnaToProteinMass = rnaMass / proteinMass


			## Ribosome counts and statistics ##

			# Get ids for 30S and 50S subunits
			proteinIds30S = sim_data.moleculeGroups.s30_proteins
			rnaIds30S = [sim_data.process.translation.monomerData['rnaId'][np.where(sim_data.process.translation.monomerData['id'] == pid)[0][0]] for pid in proteinIds30S]
			rRnaIds30S = sim_data.moleculeGroups.s30_16sRRNA
			complexIds30S = [sim_data.moleculeIds.s30_fullComplex]

			proteinIds50S = sim_data.moleculeGroups.s50_proteins
			rnaIds50S = [sim_data.process.translation.monomerData['rnaId'][np.where(sim_data.process.translation.monomerData['id'] == pid)[0][0]] for pid in proteinIds50S]
			rRnaIds50S = sim_data.moleculeGroups.s50_23sRRNA
			rRnaIds50S.extend(sim_data.moleculeGroups.s50_5sRRNA)
			complexIds50S = [sim_data.moleculeIds.s50_fullComplex]

			# Get indexes for 30S and 50S subunits based on ids
			bulkMolecules = TableReader(os.path.join(simOutDir, "BulkMolecules"))
			moleculeIds = bulkMolecules.readAttribute("objectNames")
			proteinIndexes30S = np.array([moleculeIds.index(protein) for protein in proteinIds30S], np.int)
			rnaIndexes30S = np.array([moleculeIds.index(rna) for rna in rnaIds30S], np.int)
			rRnaIndexes30S = np.array([moleculeIds.index(rRna) for rRna in rRnaIds30S], np.int)
			complexIndexes30S = np.array([moleculeIds.index(comp) for comp in complexIds30S], np.int)

			proteinIndexes50S = np.array([moleculeIds.index(protein) for protein in proteinIds50S], np.int)
			rnaIndexes50S = np.array([moleculeIds.index(rna) for rna in rnaIds50S], np.int)
			rRnaIndexes50S = np.array([moleculeIds.index(rRna) for rRna in rRnaIds50S], np.int)
			complexIndexes50S = np.array([moleculeIds.index(comp) for comp in complexIds50S], np.int)

			# Get counts of 30S and 50S mRNA, rProteins, rRNA, and full complex counts
			initialTime = TableReader(os.path.join(simOutDir, "Main")).readAttribute("initialTime")
			freeProteinCounts30S = bulkMolecules.readColumn("counts")[:, proteinIndexes30S]
			rnaCounts30S = bulkMolecules.readColumn("counts")[:, rnaIndexes30S]
			freeRRnaCounts30S = bulkMolecules.readColumn("counts")[:, rRnaIndexes30S]
			complexCounts30S = bulkMolecules.readColumn("counts")[:, complexIndexes30S]

			freeProteinCounts50S = bulkMolecules.readColumn("counts")[:, proteinIndexes50S]
			rnaCounts50S = bulkMolecules.readColumn("counts")[:, rnaIndexes50S]
			freeRRnaCounts50S = bulkMolecules.readColumn("counts")[:, rRnaIndexes50S]
			complexCounts50S = bulkMolecules.readColumn("counts")[:, complexIndexes50S]

			bulkMolecules.close()

			# Get active ribosome counts
			uniqueMoleculeCounts = TableReader(os.path.join(simOutDir, "UniqueMoleculeCounts"))

			ribosomeIndex = uniqueMoleculeCounts.readAttribute("uniqueMoleculeIds").index("activeRibosome")
			activeRibosome = uniqueMoleculeCounts.readColumn("uniqueMoleculeCounts")[:, ribosomeIndex]

			uniqueMoleculeCounts.close()

			# Get elongation rate data
			ribosomeDataFile = TableReader(os.path.join(simOutDir, "RibosomeData"))
			actualElongations = ribosomeDataFile.readColumn("actualElongations")
			ribosomeDataFile.close()

			# Calculate statistics
			rProteinCounts = np.hstack((freeProteinCounts50S, freeProteinCounts30S))
			limitingCountThreshold = 15
			limitingRProteinIdxs = np.unique(np.where(rProteinCounts < limitingCountThreshold)[1])
			limitingRProteinCounts = rProteinCounts[:, limitingRProteinIdxs] # Get traces of limiting rProteins

			rRnaCounts = np.hstack((freeRRnaCounts50S, freeRRnaCounts30S))
			rRnaCounts = rRnaCounts[:, np.unique(np.where(rRnaCounts > 0)[1])] # Get only non-zero for all time counts

			counts30S = complexCounts30S
			counts50S = complexCounts50S

			ribosomeCounts = activeRibosome

			effectiveElongationRate = actualElongations / ribosomeCounts
			extraRibosomes = (ribosomeCounts - actualElongations / 21.) / (actualElongations / 21.) * 100

			fractionActive = activeRibosome.astype(np.float) / (activeRibosome + np.hstack((counts30S, counts50S)).min(axis=1))

			## Calculate statistics involving ribosomes and RNAP ##
			ratioRNAPtoRibosome = totalRnap.astype(np.float) / ribosomeCounts.astype(np.float)
			ribosomeConcentration = ((1 / sim_data.constants.nAvogadro) * ribosomeCounts) / ((1.0 / sim_data.constants.cellDensity) * (units.fg * cellMass))

			averageRibosomeElongationRate = TableReader(os.path.join(simOutDir, "RibosomeData")).readColumn("effectiveElongationRate")
			processElongationRate = TableReader(os.path.join(simOutDir, "RibosomeData")).readColumn("processElongationRate")


			## Calculate statistics involving ribosome efficiency ##
			aaUsed = TableReader(os.path.join(simOutDir, "GrowthLimits")).readColumn("aasUsed")
			aaAllocated = TableReader(os.path.join(simOutDir, "GrowthLimits")).readColumn("aaAllocated")
			aaRequested = TableReader(os.path.join(simOutDir, "GrowthLimits")).readColumn("aaRequestSize")
			aaPoolsize = TableReader(os.path.join(simOutDir, "GrowthLimits")).readColumn("aaPoolSize")

			allocatedRibosomes = TableReader(os.path.join(simOutDir, "GrowthLimits")).readColumn("activeRibosomeAllocated")
			allocatedElongationRate = aaUsed.sum(axis=1) / allocatedRibosomes * timeStep.asNumber(units.s)

			## Load other data
			translationSupply = TableReader(os.path.join(simOutDir, "RibosomeData")).readColumn("translationSupply")


			## Plotting ##

			width = 100

			# Plot growth rate
			avgDoublingTime = doublingTime[1:].asNumber(units.min).mean()
			stdDoublingTime = doublingTime[1:].asNumber(units.min).std()
			ax1.plot(time.asNumber(units.min), doublingTime.asNumber(units.min))
			ax1.plot(time.asNumber(units.min), expected_doubling_time.asNumber(units.min) * np.ones(time.asNumber().size), linestyle='--')
			ax1.plot(time.asNumber(units.min), np.convolve(doublingTime.asNumber(units.min), np.ones(width) / width, mode = "same"))
			if gen == 0:
				y_lim = [avgDoublingTime - 2*stdDoublingTime, avgDoublingTime + 2*stdDoublingTime]
			else:
				y_lim = get_new_ylim(ax1, avgDoublingTime - 2*stdDoublingTime, avgDoublingTime + 2*stdDoublingTime)
			ax1.set_ylim(y_lim)
			ax1.set_ylabel("Doubling\ntime (min)")
			ax1.axvline(x = time.asNumber(units.min).max(), linewidth=2, color='k', linestyle='--')

			hist_doublingTime = removeNanReshape(doublingTime.asNumber(units.min))
			nbins = int(np.ceil(np.sqrt(hist_doublingTime.size)))
			ax1_1.hist(hist_doublingTime, nbins, (hist_doublingTime.mean() - hist_doublingTime.std() / 2, hist_doublingTime.mean() + hist_doublingTime.std() / 2))

			# Plot RNAP active fraction
			ax2.plot(time.asNumber(units.min), fractionRnapActive)
			ax2.plot(time.asNumber(units.min), sim_data.growthRateParameters.fractionActiveRnap * np.ones(time.asNumber().size), linestyle='--')
			ax2.axvline(x = time.asNumber(units.min).max(), linewidth=2, color='k', linestyle='--')
			ax2.set_ylabel("Fraction active\nRNAP")

			hist_fractionRnapActive = removeNanReshape(fractionRnapActive)
			nbins = int(np.ceil(np.sqrt(hist_fractionRnapActive.size)))
			ax2_1.hist(hist_fractionRnapActive, nbins, (hist_fractionRnapActive.mean() - hist_fractionRnapActive.std(), hist_fractionRnapActive.mean() + hist_fractionRnapActive.std()))

			# Plot RNAP active and total counts
			ax3.plot(time.asNumber(units.min), totalRnap)
			ax3.plot(time.asNumber(units.min), rnapCountsActive)
			ax3.axvline(x = time.asNumber(units.min).max(), linewidth=2, color='k', linestyle='--')
			ax3.set_ylabel("Total & active\nRNAP")

			# Plot limiting rProtein counts
			if limitingRProteinCounts.size > 0:
				ax4.plot(time.asNumber(units.min), limitingRProteinCounts)
			ax4.axvline(x = time.asNumber(units.min).max(), linewidth=2, color='k', linestyle='--')
			ax4.set_ylim([0, 100])
			ax4.set_ylabel("Limiting rProtein\ncounts")

			# Plot rRNA counts
			ax5.plot(time.asNumber(units.min), rRnaCounts)
			ax5.set_ylim([0, 200])
			ax5.axvline(x = time.asNumber(units.min).max(), linewidth=2, color='k', linestyle='--')
			ax5.set_ylabel("rRNA\ncounts")

			# Plot 30S and 50S counts
			ax6.plot(time.asNumber(units.min), counts30S)
			ax6.plot(time.asNumber(units.min), counts50S)
			ax6.set_ylim([0, np.max([counts30S[2:].max(), counts50S[2:].max()])])
			ax6.axvline(x = time.asNumber(units.min).max(), linewidth=2, color='k', linestyle='--')
			ax6.set_ylabel("30S & 50S\ncounts")

			# Plot ribosome concentration
			ax7.plot(time.asNumber(units.min), ribosomeConcentration.asNumber(units.mmol / units.L))
			ax7.axvline(x = time.asNumber(units.min).max(), linewidth=2, color='k', linestyle='--')
			if gen == 0:
				y_lim = [ribosomeConcentration.asNumber(units.mmol / units.L)[10:].min(), ribosomeConcentration.asNumber(units.mmol / units.L).max()]
			else:
				y_lim = get_new_ylim(ax7, ribosomeConcentration.asNumber(units.mmol / units.L)[10:].min(), ribosomeConcentration.asNumber(units.mmol / units.L).max())
			ax7.set_ylim(y_lim)
			ax7.set_ylabel("[Active ribosome]\n(mM)")

			ax7_1 = ax7.twinx()
			ax7_1.plot(time.asNumber(units.min), ribosomeCounts)
			if gen == 0:
				y_lim = [ribosomeCounts[10:].min(), ribosomeCounts.max()]
			else:
				y_lim = get_new_ylim(ax7_1, ribosomeCounts[10:].min(), ribosomeCounts.max())
			ax7_1.set_ylim(y_lim)
			ax7_1.set_ylabel("Active\nribosome\ncount")

			# Plot ratio
			ax8.plot(time.asNumber(units.min), ratioRnaToProteinMass)
			ax8.axvline(x = time.asNumber(units.min).max(), linewidth=2, color='k', linestyle='--')
			ax8.set_ylabel("RNA/Protein")

			# Plot translation supply rate
			ax8_1.plot(time.asNumber(units.min), translationSupply)
			ax8_1.axvline(x = time.asNumber(units.min).max(), linewidth=2, color='k', linestyle='--')
			ax8_1.set_ylabel("AA to translation\naa/s/fg")



			# Plot RNAP:ribosome ratio
			ax9.plot(time.asNumber(units.min), ratioRNAPtoRibosome)
			ax9.plot(time.asNumber(units.min), ratioRNAPtoRibosome.mean() * np.ones(time.asNumber().size), linestyle='--')
			ax9.axvline(x = time.asNumber(units.min).max(), linewidth=2, color='k', linestyle='--')
			ax9.set_ylabel("RNAP:Ribosome\ncounts")

			# Plot number of "extra" ribosomes
			ax10.plot(time.asNumber(units.min), extraRibosomes)
			ax10.axvline(x = time.asNumber(units.min).max(), linewidth=2, color='k', linestyle='--')
			ax10.set_ylim([0, 100])
			ax10.set_ylabel("% extra\nribosomes")

			# Average ribosome elongation rate
			ax11.plot(time.asNumber(units.min), averageRibosomeElongationRate)
			ax11.plot(time.asNumber(units.min), np.convolve(averageRibosomeElongationRate, np.ones(width) / width, mode = "same"))
			ax11.axvline(x = time.asNumber(units.min).max(), linewidth=2, color='k', linestyle='--')
			if gen == 0:
				y_lim = [averageRibosomeElongationRate[100:].min(), averageRibosomeElongationRate[100:].max()]
			else:
				y_lim = get_new_ylim(ax11, averageRibosomeElongationRate[100:].min(), averageRibosomeElongationRate[100:].max())
			ax11.set_ylim(y_lim)
			ax11.set_ylabel("Eff. ribosome\nelongation rate\n(aa/s)")

			# Process elongation rate
			ax12.plot(time.asNumber(units.min), processElongationRate)
			ax12.plot(time.asNumber(units.min), np.convolve(processElongationRate, np.ones(width) / width, mode = "same"))
			ax12.axvline(x = time.asNumber(units.min).max(), linewidth=2, color='k', linestyle='--')
			if gen == 0:
				y_lim = [processElongationRate[100:].min(), processElongationRate[100:].max()]
			else:
				y_lim = get_new_ylim(ax12, processElongationRate[100:].min(), processElongationRate[100:].max())
			ax12.set_ylim(y_lim)
			ax12.set_ylabel("Process ribosome\nelongation rate\n(aa/s)")

			# Allocated AA / allocated ribosomes elongation rate
			ax13.plot(time.asNumber(units.min), allocatedElongationRate)
			ax13.plot(time.asNumber(units.min), np.convolve(allocatedElongationRate, np.ones(width) / width, mode = "same"))
			ax13.axvline(x = time.asNumber(units.min).max(), linewidth=2, color='k', linestyle='--')
			if gen == 0:
				y_lim = [allocatedElongationRate[300:].min(), allocatedElongationRate[300:].max()]
			else:
				y_lim = get_new_ylim(ax13, allocatedElongationRate[300:].min(), allocatedElongationRate[300:].max())
			ax13.set_ylim(y_lim)
			ax13.set_ylabel("Allocated\nAA / ribosomes")

			# AA requested over total pool size
			ax14.plot(time.asNumber(units.min), aaRequested / aaPoolsize)
			ax14.axvline(x = time.asNumber(units.min).max(), linewidth=2, color='k', linestyle='--')
			ax14.set_ylabel("AA request / total")

			# AA used over AA allocated
			ax15.plot(time.asNumber(units.min), aaUsed / aaAllocated)
			ax15.axvline(x = time.asNumber(units.min).max(), linewidth=2, color='k', linestyle='--')
			ax15.set_ylim([0., 1.1])
			ax15.set_ylabel("AA used / allocated")

			# Fraction active ribosomes
			ax16.plot(time.asNumber(units.min), fractionActive)
			ax16.axvline(x = time.asNumber(units.min).max(), linewidth=2, color='k', linestyle='--')
			if gen == 0:
				y_lim = [np.nanmin(fractionActive[10:]), np.nanmax(fractionActive) + 0.01]
			else:
				y_lim = get_new_ylim(ax16, np.nanmin(fractionActive[10:]), np.nanmax(fractionActive) + 0.01)
			ax16.set_ylim(y_lim)
			ax16.set_ylabel("Fraction active\nribosome")

		ax16.set_xlabel("Time (min)")

		fig.subplots_adjust(hspace=.5, wspace = 0.3)

		exportFigure(plt, plotOutDir, plotOutFileName,metadata)
		plt.close("all")

def getMassData(simDir, massNames):
	simOutDir = os.path.join(simDir, "simOut")

	time = TableReader(os.path.join(simOutDir, "Main")).readColumn("time")

	mass = TableReader(os.path.join(simOutDir, "Mass"))

	massFractionData = np.zeros((len(massNames),time.size))

	for idx, massType in enumerate(massNames):
		massFractionData[idx,:] = mass.readColumn(massNames[idx])

	if len(massNames) == 1:
		massFractionData = massFractionData.reshape(-1)

	return time, massFractionData

def get_new_ylim(axis, new_min, new_max):
	ymin = axis.get_ylim()[0]
	ymax = axis.get_ylim()[1]

	if new_min < ymin:
		ymin = new_min
	if new_max > ymax:
		ymax = new_max

	return [ymin, ymax]

def removeNanReshape(a):
	return a[np.logical_not(np.isnan(a))]


if __name__ == "__main__":
	Plot().cli()
