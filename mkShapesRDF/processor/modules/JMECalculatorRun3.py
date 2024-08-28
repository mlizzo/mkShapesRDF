import ROOT
from mkShapesRDF.processor.framework.module import Module


class JMECalculator(Module):
    """
    This module calculates the JES/JER for jets and MET objects and stores the nominal values and the variations (up/down) in the output tree.
    """

    def __init__(
        self,
        jsonFile,
        JEC_era,
        JER_era,
		jsonFileSmearingTool,
        jet_object,
        met_collections=["PuppiMET"],
        do_Jets=True,
        do_MET=True,
        do_JER=True,
        do_Unclustered=True,
        store_nominal=True,
        store_variations=True,
    ):
        """
        JMECalculator module

        Parameters
        ----------
        jsonFile : str
            path to json file for JEC and JER
        JEC_era : str
            JEC era to use
        JER_era : str
            JER era to use
        jsonFileSmearingTool : str
            path to json file to smearing tool
        jet_object : str
            Jet Collection to use (e.g. ``CleanJet``)
        met_collections : list, optional, default: ``["PuppiMET", "MET"]``
            MET collections to use
        do_Jets : bool, optional, default: ``True``
            Whether to calculate JES/JER for jets
        do_MET : bool, optional, default: ``True``
            Whether to calculate JES/JER for MET objects
        do_JER : bool, optional, default: ``True``
            Whether to calculate JER
        store_nominal : bool, optional, default: ``True``
            Whether to store the nominal values (corrected or smeared)
        store_variations : bool, optional
            Whether to store the variations (up/down) for JES/JER
        """
        super().__init__("JMECalculator")
        self.json = jsonFile
        self.JEC_era = JEC_era
        self.JER_era = JER_era
        self.jsonFileSmearingTool = jsonFileSmearingTool
        self.jet_object = jet_object
        self.met_collections = met_collections
        self.do_Jets = do_Jets
        self.do_MET = do_MET
        self.do_JER = do_JER
        self.do_Unclustered = do_Unclustered
        self.store_nominal = store_nominal
        self.store_variations = store_variations

    def runModule(self, df, values):
        ROOT.gInterpreter.Declare(
            """
            using namespace ROOT;

            RVecU revertIndicesMask(RVecU sortedIndices, uint size){
                auto tmp = ROOT::VecOps::Range(size);
                RVecU r {};

                for (uint i = 0; i < tmp.size(); i++){
                    for (uint j = 0; j < sortedIndices.size(); j++){
                        if (tmp[i] == sortedIndices[j]){
                            r.push_back(j);
                        }
                    }
                }
                return r;

            }
        """
        )
        
        from CMSJMECalculators import loadJMESystematicsCalculators

        loadJMESystematicsCalculators()
        
        jsonFile 	= self.json
        jetAlgo 	= self.jet_object
        jecTag  	= self.JEC_era
        jerTag 		= ""
        jsonFileSmearingTool = self.jsonFileSmearingTool
        jecLevel    = "L1L2L3Res"
        L1JecTag    = ""
        ROOT.gROOT.ProcessLine("std::vector<string> jesUnc{}")
        jesUnc = getattr(ROOT, "jesUnc")
        jesUnc.push_back("Total")
        addHEM      = "false"
        smearingTool= "JERSmear"
        maxDR       = 0.2
        maxDPT      = 3
        
        if self.do_MET:
            L1JecTag        = "L1FastJet"
            unclEnThr       = 15.
            emEnFracThr     = 0.9
            isT1smearedMET  = "false"
            for MET in self.met_collections:
                if self.do_JER and "Puppi" in MET:
                    jerTag          = self.JER_era
                    isT1smearedMET  = "true"
                ROOT.gROOT.ProcessLine(f"Type1METVariationsCalculator my{MET}VarCalc = Type1METVariationsCalculator::create(\"{jsonFile}\", \"{jetAlgo}\", \"{jecTag}\", \"{jecLevel}\", \"{L1JecTag}\", {unclEnThr}, {emEnFracThr}, {jesUnc}, {addHEM}, {isT1smearedMET}, \"{jerTag}\", \"{jsonFileSmearingTool}\", \"{smearingTool}\", false, true, {maxDR}, {maxDPT});")
                calcMET = getattr(ROOT, f"my{MET}VarCalc")
                METSources = calcMET.available()
                METSources = calcMET.available()[1:][::2]
                METSources = [str(source).replace('up', '') for source in METSources]
                print(METSources)
                '''
                jesSources = calcMET.available()
                skip = 1
                if self.do_JER and "Puppi" not in MET:
                    skip += 6 * 2
                # first are JERs, last two are unclustered unc.
                jesSources = jesSources[skip:-2][::2]
                jesSources = list(map(lambda k: str(k)[3:-2], jesSources))
                # jesSources = sorted(jesSources)
                jesSources = list(map(lambda k: "JES_" + k, jesSources))
                print(jesSources)
                '''
                # list of columns to be passed to myJetVarCal produce
                cols = []

                JetColl = "newJet"

                df = df.Define("newJet_pt", "CleanJet_pt")
                df = df.Define("newJet_eta", "CleanJet_eta")
                df = df.Define("newJet_phi", "CleanJet_phi")
                df = df.Define("newJet_jetIdx", "CleanJet_jetIdx")

                cols.append(f"{JetColl}_pt")
                cols.append(f"{JetColl}_eta")
                cols.append(f"{JetColl}_phi")
                cols.append(f"Take(Jet_mass, {JetColl}_jetIdx)")
                cols.append(f"Take(Jet_rawFactor, {JetColl}_jetIdx)")
                cols.append(f"Take(Jet_area, {JetColl}_jetIdx)")
                cols.append(f"Take(Jet_muonSubtrFactor, {JetColl}_jetIdx)")
                cols.append(f"Take(Jet_neEmEF, {JetColl}_jetIdx)")
                cols.append(f"Take(Jet_chEmEF, {JetColl}_jetIdx)")
                cols.append(f"Take(Jet_jetId, {JetColl}_jetIdx)")
    
                # rho
                cols.append("Rho_fixedGridRhoFastjetAll")

                cols.append(f"Take(Jet_genJetIdx, {JetColl}_jetIdx)")
                cols.append(f"Take(Jet_partonFlavour, {JetColl}_jetIdx)")
                # seed
                cols.append(
                    f"(run<<20) + (luminosityBlock<<10) + event + 1 + int({JetColl}_eta.size()>0 ? {JetColl}_eta[0]/.01 : 0)"
                )

                # gen jet coll
                cols.append("GenJet_pt")
                cols.append("GenJet_eta")
                cols.append("GenJet_phi")
                cols.append("GenJet_mass")

                RawMET = "RawMET" if "Puppi" not in MET else "RawPuppiMET"
                cols.append(f"{RawMET}_phi")
                cols.append(f"{RawMET}_pt")

                df = df.Define('EmptyLowPtJet', 'ROOT::RVecF{}')
                cols.append("CorrT1METJet_rawPt")
                cols.append("CorrT1METJet_eta")
                cols.append("CorrT1METJet_phi")
                cols.append("CorrT1METJet_area")
                cols.append("CorrT1METJet_muonSubtrFactor")
                cols.append("ROOT::RVecF {}")
                cols.append("ROOT::RVecF {}")
                
                cols.append("MET_MetUnclustEnUpDeltaX")
                cols.append("MET_MetUnclustEnUpDeltaY")

                df = df.Define(
                    f"{MET}Vars", f"my{MET}VarCalc.produce({', '.join(cols)})"
                )
                
                if self.store_nominal:
                    df = df.Define(f"{MET}_pt", f"CleanJet_pt.size() > 0 ? {MET}Vars.pt(0) : {RawMET}_pt")
                    df = df.Define(f"{MET}_phi", f"CleanJet_pt.size() > 0 ? {MET}Vars.phi(0) : {RawMET}_phi")
                
                if self.store_variations:
                    '''
                    _sources = []
                    if self.do_JER and "Puppi" not in MET:
                        _sources = [f"JER_{i}" for i in range(6)]
                    _sources += jesSources
                    sources = _sources.copy()
                    METsources = _sources.copy()
                    if self.do_Unclustered:
                        METsources += ["MET"]  # last one is the unclustered variation
                    print("\n")
                    print("MET uncertainties: ")
                    print(METsources)
                    '''
                    for variable in [MET + "_pt", MET + "_phi"]:
                        for i, source in enumerate(METSources):
                            up = f"{MET}Vars.{variable.split('_')[-1]}({2*i+1})"
                            do = f"{MET}Vars.{variable.split('_')[-1]}({2*i+1+1})"
                            df = df.Vary(
                                variable,
                                "ROOT::RVecD{" + up + ", " + do + "}",
                                ["up", "do"],
                                source,
                            )
                df = df.DropColumns(f"{MET}Vars*")
                print("MET variables run succesfully!")

        if self.do_Jets:
            if self.do_JER:
                jerTag          = self.JER_era
            ROOT.gROOT.ProcessLine(f"JetVariationsCalculator myJetVariationsCalculator = JetVariationsCalculator::create(\"{jsonFile}\", \"{jetAlgo}\", \"{jecTag}\", \"{jecLevel}\", {jesUnc}, {addHEM}, \"{jerTag}\", \"{jsonFileSmearingTool}\", \"{smearingTool}\", false, true, {maxDR}, {maxDPT});")
            calc = getattr(ROOT, "myJetVariationsCalculator")
            jesSources = calc.available()
            jesSources = calc.available()[1:][::2]
            jesSources = [str(source).replace('up', '') for source in jesSources]
            print(jesSources)
            '''
            skip = 1
            if self.do_JER and "Puppi" in MET:
                skip += 1 * 2
            # first are JERs, last two are unclustered unc.
            jesSources = jesSources[skip:-2]
            jesSources = list(map(lambda k: str(k).replace("jes", "JES"), jesSources))
            '''
            # list of columns to be passed to myJetVarCal produce
            cols = []

            # nre reco jet coll
            JetColl = "newJet"

            df = df.Define("newJet_pt", "CleanJet_pt")
            df = df.Define("newJet_eta", "CleanJet_eta")
            df = df.Define("newJet_phi", "CleanJet_phi")
            df = df.Define("newJet_jetIdx", "CleanJet_jetIdx")

            cols.append(f"{JetColl}_pt")
            cols.append(f"{JetColl}_eta")
            cols.append(f"{JetColl}_phi")
            cols.append("CleanJet_mass")
            cols.append(f"Take(Jet_rawFactor, {JetColl}_jetIdx)")
            cols.append(f"Take(Jet_area, {JetColl}_jetIdx)")
            cols.append(f"Take(Jet_jetId, {JetColl}_jetIdx)")

            # rho
            cols.append("Rho_fixedGridRhoFastjetAll")

            cols.append(f"Take(Jet_genJetIdx, {JetColl}_jetIdx)")
            cols.append(f"Take(Jet_partonFlavour, {JetColl}_jetIdx)")

            # seed
            cols.append(
                f"(run<<20) + (luminosityBlock<<10) + event + 1 + int({JetColl}_eta.size()>0 ? {JetColl}_eta[0]/.01 : 0)"
            )

            # gen jet coll
            cols.append("GenJet_pt")
            cols.append("GenJet_eta")
            cols.append("GenJet_phi")
            cols.append("GenJet_mass")

            df = df.Define("jetVars", f'myJetVariationsCalculator.produce({", ".join(cols)})')
            if self.store_nominal:
                df = df.Define("CleanJet_pt", "jetVars.pt(0)")
                df = df.Define("CleanJet_mass", "jetVars.mass(0)")
                df = df.Define(
                    "CleanJet_sorting",
                    "ROOT::VecOps::Reverse(ROOT::VecOps::Argsort(CleanJet_pt))",
                )

                df = df.Define("CleanJet_pt", "Take( CleanJet_pt, CleanJet_sorting)")
                df = df.Define("CleanJet_eta", "Take( CleanJet_eta, CleanJet_sorting)")
                df = df.Define("CleanJet_phi", "Take( CleanJet_phi, CleanJet_sorting)")
                df = df.Define("CleanJet_mass", "Take( CleanJet_mass, CleanJet_sorting)")
                df = df.Define("CleanJet_jetIdx", "Take( CleanJet_jetIdx, CleanJet_sorting)")

            else:
                df = df.Define(
                    "CleanJet_sorting",
                    "Range(CleanJet_pt.size())",
                )

            if self.store_variations:
                '''
                _sources = []
                if self.do_JER:
                    _sources = [f"JER_{i}" for i in range(6)]
                _sources += jesSources
                sources = _sources.copy()
                print("\n")
                print("JES uncertainties: ")
                print(sources)
                '''
                for i, source in enumerate(jesSources):
                    variations_pt = []
                    variations_jetIdx = []
                    variations_mass = []
                    variations_phi = []
                    variations_eta = []
                    for j, tag in enumerate(["up", "down"]):
                        variation_pt = f"jetVars.pt({2*i+1+j})"
                        variation_mass = f"jetVars.mass({2*i+1+j})"
                        df = df.Define(
                            f"tmp_CleanJet_pt__JES_{source}_{tag}",
                            variation_pt,
                        )
                        df = df.Define(
                            f"tmp_CleanJet_pt__JES_{source}_{tag}_sorting",
                            f"ROOT::VecOps::Reverse(ROOT::VecOps::Argsort(tmp_CleanJet_pt__JES_{source}_{tag}))",
                        )
                        variations_pt.append(
                            f"Take(tmp_CleanJet_pt__JES_{source}_{tag}, tmp_CleanJet_pt__JES_{source}_{tag}_sorting)"
                        )

                        df = df.Define(
                            f"CleanJet_cleanJetIdx_preJES_{source}_{tag}",
                            f"tmp_CleanJet_pt__JES_{source}_{tag}_sorting",
                        )

                        variations_jetIdx.append(
                            f"Take({JetColl}_jetIdx, tmp_CleanJet_pt__JES_{source}_{tag}_sorting)",
                        )

                        df = df.Define(
                            f"tmp_CleanJet_mass__JES_{source}_{tag}",
                            f"Take({variation_mass}, tmp_CleanJet_pt__JES_{source}_{tag}_sorting)",
                        )
                        variations_mass.append(f"tmp_CleanJet_mass__JES_{source}_{tag}")

                        variations_phi.append(
                            f"Take({JetColl}_phi, tmp_CleanJet_pt__JES_{source}_{tag}_sorting)"
                        )
                        variations_eta.append(
                            f"Take({JetColl}_eta, tmp_CleanJet_pt__JES_{source}_{tag}_sorting)"
                        )

                    tags = ["up", "do"]
                    df = df.Vary(
                        "CleanJet_pt",
                        "ROOT::RVec<ROOT::RVecF>{"
                        + variations_pt[0]
                        + ", "
                        + variations_pt[1]
                        + "}",
                        tags,
                        source,
                    )

                    df = df.Vary(
                        "CleanJet_jetIdx",
                        "ROOT::RVec<ROOT::RVecI>{" + variations_jetIdx[0]
                        + ", " + variations_jetIdx[1]
                        + "}",
                        tags,
                        source,
                    )

                    df = df.Vary(
                        "CleanJet_mass",
                        "ROOT::RVec<ROOT::RVecF>{" + variations_mass[0]
                        + ", " + variations_mass[1]
                        + "}",
                        tags,
                        source,
                    )

                    df = df.Vary(
                        "CleanJet_phi",
                        "ROOT::RVec<ROOT::RVecF>{" + variations_phi[0]
                        + ", " + variations_phi[1]
                        + "}",
                        tags,
                        source,
                    )

                    df = df.Vary(
                        "CleanJet_eta",
                        "ROOT::RVec<ROOT::RVecF>{" + variations_eta[0]
                        + ", " + variations_eta[1]
                        + "}",
                        tags,
                        source,
                    )

                    df = df.DropColumns("tmp_*")

            df = df.DropColumns("jetVars*")
            df = df.DropColumns("CleanJet_sorting")
        return df
