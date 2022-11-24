#include "DataFormats/Common/interface/Wrapper.h"

//Add includes for your classes here
#include "MiniAOD/BoostedObjects/interface/BoostedJet.h"

#include <vector>

namespace {

  struct Boosted_Collections {

    //add 'dummy' Wrapper variable for each class type you put into the Event
    boosted::BoostedJet boostedjetdummy0;
    edm::Wrapper<boosted::BoostedJet> boostedjetdummy1;
    std::vector<boosted::BoostedJet> boostedjetdummy2;
    edm::Wrapper<std::vector<boosted::BoostedJet> > boostedjetdummy3;
  };
}
