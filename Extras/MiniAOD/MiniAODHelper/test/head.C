{
gROOT->Reset();

gSystem->Load("libFWCoreFWLite.so");
AutoLibraryLoader::enable();
gSystem->Load("libDataFormatsFWLite.so");
gSystem->Load("libDataFormatsPatCandidates.so");
gSystem->Load("libDataFormatsCommon.so");
gSystem->Load("libDataFormatsProvenance.so");
gSystem->Load("libDataFormatsMuonReco.so");
gSystem->Load("libDataFormatsTrackReco.so");
gSystem->Load("libDataFormatsCandidate.so");
gSystem->Load("libMiniAODMiniAODHelper.so");

}
